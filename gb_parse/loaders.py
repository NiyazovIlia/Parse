import re
from urllib.parse import urljoin
from scrapy import Selector
from scrapy.loader import ItemLoader
from .items import HHItem
from itemloaders.processors import TakeFirst, MapCompose

def union(item):
    a = [''.join(item)]
    return a[0]



class HHLoader(ItemLoader):
    default_item_class = HHItem
    title_out = TakeFirst()
    url_out = TakeFirst()
    skill_out = union
    description_out = union
    price_out = union
    author_out = TakeFirst()