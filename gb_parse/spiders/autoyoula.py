import pymongo
import scrapy
import bs4
import requests
from ..loaders import AutoyoulaLoader


class AutoyoulaSpider(scrapy.Spider):
    name = "autoyoula"
    allowed_domains = ["auto.youla.ru"]
    start_urls = ["https://auto.youla.ru/"]

    css_query = {
        "brands": "div.ColumnItemList_container__5gTrc a.blackLink",
        "pagination": "div.Paginator_block__2XAPy a.Paginator_button__u1e7D",
        "ads": "article.SerpSnippet_snippet__3O1t2 a.SerpSnippet_name__3F7Yu",
    }

    # // означают, что где-то в верстке есть что-то
    # любые элементы типа class, id и так далее пишутся в [@...] после в конце пишется /text() для получения текста
    # или через @ пишется тег который нужно получить
    # contains позволяет найти что-то определенное если классов к примеру несколько
    # если каких-то данных несколько, то лучше взять блок в котором они все находятся, а потом в loader
    # сделать функцию, которая вытащит данные по отдельности
    data_xpath = {
        'title': "//div[@data-target='advert']//div[@data-target='advert-title']/text()",
        'price': "//div[@data-target='advert-price']/text()",
        'images': '//figure[contains(@class, "PhotoGallery_photo")]//img/@src',
        'specification': '//h3[contains(text(), "Характеристики")]/../div/div',
        'author': '//body/script[contains(text(), "window.transitState = decodeURIComponent")]',
        'description': "//div[@data-target='advert-info-descriptionFull']/text()",
    }

    @staticmethod
    def gen_task(response, link_list, callback):
        for link in link_list:
            yield response.follow(link.attrib["href"], callback=callback)

    def parse(self, response, **kwargs):
        brands_links = response.css(self.css_query["brands"])
        yield from self.gen_task(response, brands_links, self.brand_parse)

    def brand_parse(self, response):
        pagination_links = response.css(self.css_query["pagination"])
        yield from self.gen_task(response, pagination_links, self.brand_parse)
        ads_links = response.css(self.css_query["ads"])
        yield from self.gen_task(response, ads_links, self.ads_parse)

    # тут происходит загрузка данных на странице и передача в AutoyoulaLoader (для корректировки данных)
    def ads_parse(self, response):
        #  loader.add_css делает getall, возвращает все значения которые найдет
        loader = AutoyoulaLoader(response=response)
        for key, selector in self.data_xpath.items():
            loader.add_xpath(key, selector)
        loader.add_value('url', response.url)
        yield loader.load_item()
