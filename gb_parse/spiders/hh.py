import scrapy
from ..loaders import HHLoader


class HhSpider(scrapy.Spider):
    name = 'hh'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?area=1']

    xpath_query = {
        "pagination": "//span[@class='bloko-button-group']//a[contains(@class, 'bloko-button')]",
        "author": "//div[@class='vacancy-serp-item__sidebar']//a[@data-qa='vacancy-serp__vacancy-employer-logo']",
        "ads": "//span[@class='g-user-content']//a[contains(@class, 'bloko-link')]",
    }

    data_xpath = {
        'title': "//h1/text()",
        'price': "//p[@class='vacancy-salary']/span[contains(@class, 'bloko-header-2')]/text()",
        'description': "//div[@class='vacancy-description']//div[@class='g-user-content']//text()",
        'skill': "//div[@class='bloko-tag-list']//span[contains(@class, 'bloko-tag__section')]/text()",
        # 'author': "//div[@class='vacancy-company-logo']/a/",
    }

    @staticmethod
    def gen_task(response, link_list, callback):
        for link in link_list:
            yield response.follow(link.attrib["href"], callback=callback)

    def parse(self, response, **kwargs):
        pagination_links = response.xpath(self.xpath_query["pagination"])
        yield from self.gen_task(response, pagination_links, self.parse)
        author_links = response.xpath(self.xpath_query["author"])
        yield from self.gen_task(response, author_links, self.parse)
        ads_links = response.xpath(self.xpath_query["ads"])
        yield from self.gen_task(response, ads_links, self.ads_parse)

    def ads_parse(self, response):
        loader = HHLoader(response=response)
        for key, selector in self.data_xpath.items():
            loader.add_xpath(key, selector)
        loader.add_value('url', response.url)
        author = response.css("div.vacancy-company-logo a").attrib.get('href')
        author_new = f'https://hh.ru/{author}'
        loader.add_value('author', author_new)
        yield loader.load_item()
