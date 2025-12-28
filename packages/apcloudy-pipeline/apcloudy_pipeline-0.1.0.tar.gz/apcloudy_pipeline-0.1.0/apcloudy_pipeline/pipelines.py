from scrapy import Item

from .client import APCloudyClient


class APCloudyItemPipeline:
    """Scrapy item pipeline to send items to AP Cloudy backend"""

    def open_spider(self, spider):
        self.client = APCloudyClient()

    def process_item(self, item: Item, spider):
        self.client.send_item(dict(item))
        return item
