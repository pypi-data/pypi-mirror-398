# Apcloudy-Pipeline

apcloudy-pipeline is a Scrapy integration that sends **items, requests, logs, and spider statistics**
to the **Your backend** using **secure HMAC-based authentication**.

---

## Features

- 📦 Item forwarding using Scrapy Item Pipeline
- 🌐 Request and response logging
- 📊 Spider statistics reporting
- 🧾 Spider, user, and Scrapy internal log forwarding
- 🔐 HMAC-secured API communication

---

## Installation

```bash
pip install apcloudy-pipeline
```
## Configuration
Add the following settings to your Scrapy project's settings.py file:
```python
APCLOUDY_API_URL = "http://localhost:8000/api/v1/"
APCLOUDY_API_KEY = "api_test_1234567890"
APCLOUDY_SECRET_KEY = "secret_test_1234567890"
JOB_ID = 123
```

### Item Pipeline (Required)
The item pipeline is required to send scraped items to the backend.
```python
ITEM_PIPELINES = {
    "apcloudy_pipeline.pipelines.APCloudyItemPipeline": 300,
}
```
### Extensions (Optional)
Enable the following extensions if you want to send requests, logs, and spider statistics.
```python
EXTENSIONS = {
    "apcloudy_pipeline.request_logger.APCloudyRequestLogger": 400,
    "apcloudy_pipeline.extensions.APCloudyLoggingExtension": 510,
    "apcloudy_pipeline.extensions.APCloudyStatsExtension": 520,
}
```

## Extensions Overview

- APCloudyRequestLogger
Captures request and response metadata such as URL, HTTP method, status code, timing, and fingerprint.

- APCloudyLoggingExtension
Sends spider logs, user logs, Scrapy internal logs, and exception tracebacks to the backend.

- APCloudyStatsExtension
Sends final spider statistics when the crawl finishes.