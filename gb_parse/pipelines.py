# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
import os

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


#  тут происходит сохранение данных


class GbParsePipeline:
    def process_item(self, item, spider):
        return item


class SaveToMongoPipeline:
    def __init__(self):
        client = pymongo.MongoClient(os.getenv('DATA_BASE_URL'))
        self.db = client['gb_parse']

    def process_item(self, item, spider):
        self.db[type(item).__name__].insert_one(item)
        return item

class GbImagePipeLine(ImagesPipeline):
    def get_media_requests(self, item, info):
        for image_url in item.get('img', []):
            yield Request(image_url)

    def item_completed(self, results, item, info):
        if results:
            item['img'] = [itm[1] for itm in results]
        return item