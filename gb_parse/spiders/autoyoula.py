import pymongo
import scrapy
import bs4
import requests


class AutoyoulaSpider(scrapy.Spider):
    name = "autoyoula"
    allowed_domains = ["auto.youla.ru"]
    start_urls = ["https://auto.youla.ru/"]

    css_query = {
        "brands": "div.ColumnItemList_container__5gTrc a.blackLink",
        "pagination": "div.Paginator_block__2XAPy a.Paginator_button__u1e7D",
        "ads": "article.SerpSnippet_snippet__3O1t2 a.SerpSnippet_name__3F7Yu",
    }

    @staticmethod
    def gen_task(response, link_list, callback):
        for link in link_list:
            yield response.follow(link.attrib["href"], callback=callback)

    data_query = {
        "title": lambda resp: resp.css("div.AdvertCard_advertTitle__1S1Ak::text").get(),
        "price": lambda resp: float(resp.css('div.AdvertCard_price__3dDCr::text').get().replace("\u2009", '')),
        # 'author':
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_client = pymongo.MongoClient()

    def parse(self, response, **kwargs):
        brands_links = response.css(self.css_query["brands"])
        yield from self.gen_task(response, brands_links, self.brand_parse)

    def brand_parse(self, response):
        pagination_links = response.css(self.css_query["pagination"])
        yield from self.gen_task(response, pagination_links, self.brand_parse)
        ads_links = response.css(self.css_query["ads"])
        yield from self.gen_task(response, ads_links, self.ads_parse)

    def ads_parse(self, response):
        data = {}
        print(response.url)
        for key, selector in self.data_query.items():
            try:
                data[key] = selector(response)
            except (ValueError, AttributeError):
                continue
        self.description_parse(response.url, data)
        self.img_parse(response.url, data)
        self.db_client['gb_parse_youla'][self.name].insert_one(data)

    def description_parse(self, url, data):
        response = requests.get(url)
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        description = soup.find_all('div', attrs={'class': 'AdvertSpecs_row__ljPcX'})
        for i in description:
            description_1 = i.find('div', attrs={'class': 'AdvertSpecs_label__2JHnS'}).text
            description_2 = i.find('div', attrs={'class': 'AdvertSpecs_data__xK2Qx'}).text
            data[description_1] = description_2
        return data

    def img_parse(self, url, data):
        array = []
        response = requests.get(url)
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        a = soup.find('div', attrs={'class': 'PhotoGallery_photoWrapper__3m7yM'})
        for i in a:
            b = i.find_all('img', attrs={'class': 'PhotoGallery_photoImage__2mHGn'})
            for j in b:
                array.append(j['src'])
            data['img'] = array
        return data
