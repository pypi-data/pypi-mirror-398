import json
import requests
from .utils import get_timestamp, hmac_signature, _json_serialize
from .exceptions import APCloudyPipelineError


class APCloudyClient:
    """
    Manages interaction with the AP Cloudy API for sending various types of data.

    This class provides methods for sending requests, items, logs, and statistical data to the
    AP Cloudy backend. It handles API authentication, including signature generation and
    request header management. It ensures that all necessary credential information is
    configured before usage, raising errors otherwise.
    """

    def __init__(self, crawler):
        # Load settings from crawler (includes spider args)
        settings = crawler.settings
        spider = crawler.spider

        self.api_url = settings.get("APCLOUDY_API_URL")
        self.public_key = settings.get("APCLOUDY_API_KEY")
        self.secret_key = settings.get("APCLOUDY_SECRET_KEY")
        # Get JOB_ID from spider args first, fallback to settings
        self.job_id = getattr(spider, 'JOB_ID', None) or settings.get("JOB_ID")

        if not all([self.api_url, self.public_key, self.secret_key, self.job_id]):
            raise APCloudyPipelineError(
                "APCloudy API credentials not found in Scrapy settings"
            )

    def _post(self, endpoint: str, payload: dict):
        """
        Sends a POST request to the specified endpoint with the provided payload.

        This method constructs the request with required headers, including
        the API key, timestamp, and signature for authentication. It formats
        the payload as JSON and sends it to the API endpoint via an HTTP POST
        request.
        """
        raw_body = json.dumps(payload)
        timestamp = get_timestamp()
        signature = hmac_signature(self.secret_key, raw_body, timestamp)

        headers = {
            "X-API-KEY": self.public_key,
            "X-TIMESTAMP": timestamp,
            "X-SIGNATURE": signature,
            "Content-Type": "application/json"
        }

        url = f"{self.api_url.rstrip('/')}?type={endpoint.lstrip('/')}"
        try:
            r = requests.post(url, headers=headers, data=raw_body, timeout=10)
            r.raise_for_status()
        except Exception as e:
            raise APCloudyPipelineError(f"Failed to send data to AP Cloudy backend: {e}")

    def send_request_log(self, request_log: dict):
        """
        Sends a log entry for a request to the specified endpoint.

        This method collects the provided request log data, combines it with
        the current job ID, and sends it to a pre-defined resource using
        an internal HTTP POST request.
        """
        payload = {"job_id": self.job_id, "data": request_log}
        return self._post("requests", payload)

    def send_item(self, item: dict):
        """
        Sends an item to be processed with the associated job.

        This method prepares the payload by combining the provided item data with the
        current job's ID. The constructed payload is then sent to the appropriate
        endpoint for processing.
        """
        payload = {"job_id": self.job_id, "data": item}
        return self._post("items", payload)

    def send_log(self, data: dict[str, str]):
        """
        Sends a log message with a specified logging level to the appropriate logging endpoint. The method constructs
        a log payload containing the job ID, log level, and message, and sends it to the endpoint using an internal
        HTTP POST request.
        """
        payload = {"job_id": self.job_id, "data": data}
        return self._post("logs", payload)

    def send_stats(self, stats: dict):
        """
        Send statistical data to the server for a specific job.

        This method compiles statistical data into a payload and posts it to a
        predefined endpoint on the server. The functionality is primarily intended
        to facilitate reporting and monitoring of job-related metrics.
        """
        safe_stats = json.loads(json.dumps(stats, default=_json_serialize))
        payload = {"job_id": self.job_id, "data": safe_stats}
        return self._post("stats", payload)
