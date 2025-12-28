from datetime import datetime
import time
import hmac
import hashlib


def hmac_signature(secret: str, raw_body: str, timestamp: str) -> str:
    """
    Compute HMAC-SHA256 signature:
    signature = HMAC_SHA256(secret, timestamp + "." + raw_body)
    """
    message = f"{timestamp}.{raw_body}".encode()
    key = secret.encode()
    signature = hmac.new(key, message, hashlib.sha256).hexdigest()
    return signature


def get_timestamp() -> str:
    """Return current timestamp in seconds"""
    return str(int(time.time()))


def _json_serialize(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)
