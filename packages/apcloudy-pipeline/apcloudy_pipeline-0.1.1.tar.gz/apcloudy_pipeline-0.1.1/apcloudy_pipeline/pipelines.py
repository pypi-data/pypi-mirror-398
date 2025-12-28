from scrapy import Item

from .client import APCloudyClient


class APCloudyItemPipeline:
    """Scrapy item pipeline to send items to AP Cloudy backend"""

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self.client = APCloudyClient(crawler)

    def process_item(self, item: Item, spider):
        self.client.send_item(dict(item))
        return item
