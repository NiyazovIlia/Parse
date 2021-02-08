# тут происходит корректировка данных
import re
from urllib.parse import urljoin
from scrapy import Selector
from scrapy.loader import ItemLoader
from .items import AutoyoulaItem, Insta
from itemloaders.processors import TakeFirst, MapCompose


def get_author_id(item):
    re_pattern = re.compile(r"youlaId%22%2C%22([a-zA-Z|\d]+)%22%2C%22avatar")
    result = re.findall(re_pattern, item)
    return result


# Map прогоняет функцию через все переданные элементы объекта

def clear_unicode(item):
    return item.replace('\u2009', '')


def get_specification(item):
    tag = Selector(text=item)
    name = tag.xpath("//div[@class='AdvertSpecs_label__2JHnS']/text()").get()
    value = tag.xpath("//div[@class='AdvertSpecs_data__xK2Qx']//text()").get()
    return {name: value}


def flat_dict(items: list) -> dict:
    result = {}
    for itm in items:
        result.update(itm)
    return result


class AutoyoulaLoader(ItemLoader):
    default_item_class = AutoyoulaItem
    url_out = TakeFirst()
    title_out = TakeFirst()
    price_in = MapCompose(clear_unicode, float)
    price_out = TakeFirst()
    author_in = MapCompose(get_author_id, lambda a_id: urljoin("https://youla.ru/user/", a_id))
    author_out = TakeFirst()
    description_out = TakeFirst()
    specification_in = MapCompose(get_specification)
    specification_out = flat_dict


class InstagramLoader(ItemLoader):
    default_item_class = Insta