# тут происходит корректировка данных
import re
from urllib.parse import urljoin
from scrapy import Selector
from scrapy.loader import ItemLoader
from .items import Insta
from itemloaders.processors import TakeFirst, MapCompose


# Map прогоняет функцию через все переданные элементы объекта


class InstagramLoader(ItemLoader):
    default_item_class = Insta
