import hashlib
import time

from scrapy import signals
from scrapy.utils.python import to_bytes
from scrapy.utils.url import canonicalize_url

from apcloudy_pipeline.client import APCloudyClient


class APCloudyRequestLogger:
    """
    Scrapy extension to log requests with detailed attributes.
    """

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        ext.client = APCloudyClient(crawler)
        crawler.signals.connect(ext.request_scheduled, signal=signals.request_scheduled)
        crawler.signals.connect(ext.response_received, signal=signals.response_received)
        crawler.signals.connect(ext.request_dropped, signal=signals.request_dropped)
        return ext

    def request_scheduled(self, request, spider):
        # Store start time in request meta
        request.meta['start_time'] = time.time()

    def response_received(self, response, request, spider):
        start_time = request.meta.get('start_time', time.time())
        response_time = time.time() - start_time

        request_log = {
            "url": request.url,
            "method": request.method,
            "status_code": response.status,
            "response_time": round(response_time, 2),
            "fingerprint": self.request_fingerprint(request),
        }

        self.client.send_request_log(request_log)

    def request_dropped(self, request, spider):
        # handle dropped requests
        request_log = {
            "url": request.url,
            "method": request.method,
            "status_code": 0,
            "response_time": 0,
            "fingerprint": self.request_fingerprint(request),
        }
        self.client.send_request_log(request_log)

    def request_fingerprint(self, request):
        """Compute request fingerprint manually if import fails"""
        fp = hashlib.sha1()
        fp.update(to_bytes(request.method))
        fp.update(to_bytes(canonicalize_url(request.url)))
        return fp.hexdigest()
