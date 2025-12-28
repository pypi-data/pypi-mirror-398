import logging
from datetime import datetime
import json

from .client import APCloudyClient


def _safe_serialize(payload):
    return json.dumps(payload, default=lambda o: o.isoformat() if isinstance(o, datetime) else str(o))


class APCloudyLogHandler(logging.Handler):
    def __init__(self, crawler, level=logging.NOTSET):
        super().__init__(level)
        self.client = APCloudyClient(crawler)
        self.formatter = logging.Formatter()

    def emit(self, record):
        if record.levelno < self.level:
            return

        log_entry = {
            "level": record.levelname,
            "message": record.getMessage(),
            "exception": None,
        }

        if record.exc_info:
            log_entry["exception"] = self.formatter.formatException(record.exc_info)

        payload_json = _safe_serialize(log_entry)
        return self.client.send_log(json.loads(payload_json))
