import json
import logging
from datetime import datetime

from scrapy import signals

from .client import APCloudyClient
from .log_handler import APCloudyLogHandler


class APCloudyStatsExtension:
    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        ext.client = APCloudyClient(crawler)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        return ext

    def spider_closed(self, spider, reason):
        try:
            stats = spider.crawler.stats.get_stats()
            # Convert non-serializable objects
            safe_stats = json.loads(
                json.dumps(stats, default=lambda o: o.isoformat() if isinstance(o, datetime) else str(o))
            )
            self.client.send_stats(safe_stats)
        except Exception as e:
            logging.error("Failed to send stats:", e)


class APCloudyLoggingExtension:
    """
    Scrapy extension to send all logs (spider/user/Scrapy internal) to AP Cloudy backend.
    """

    def __init__(self, crawler, log_level=logging.INFO):
        self.log_level = log_level
        self.handler = APCloudyLogHandler(crawler, level=log_level)

    @classmethod
    def from_crawler(cls, crawler):
        level_name = crawler.settings.get("LOG_LEVEL", "INFO")
        log_level = logging._nameToLevel.get(level_name.upper(), logging.INFO)
        ext = cls(crawler, log_level)

        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)

        return ext

    def spider_opened(self, spider):
        root_logger = logging.getLogger()

        if self.handler not in root_logger.handlers:
            root_logger.addHandler(self.handler)

        root_logger.setLevel(self.log_level)

        logging.getLogger("scrapy").propagate = True

    def spider_closed(self, spider, reason):
        root_logger = logging.getLogger()
        if self.handler in root_logger.handlers:
            root_logger.removeHandler(self.handler)
