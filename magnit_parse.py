import os
import requests
import bs4
from urllib.parse import urljoin
import pymongo
from dotenv import load_dotenv
import time


class ParseError(Exception):
    def __init__(self, text):
        self.text = text


class MagnitParse:
    def __init__(self, start_url, data_client, collect):
        self.start_url = start_url
        self.data_client = data_client
        self.data_base = self.data_client["gb_parse"]
        self.collect = collect

    # проверка доступа к сайту staticmethod
    @staticmethod
    def _get_response(url, *args, **kwargs):
        while True:
            try:
                response = requests.get(url, *args, **kwargs)
                if response.status_code > 399:
                    raise ParseError(response.status_code)
                time.sleep(0.1)
                return response
            except (requests.RequestException, ParseError):
                time.sleep(0.5)
                continue

    # получаем текст сайта staticmethod
    @staticmethod
    def _get_soup(response):
        return bs4.BeautifulSoup(response.text, 'lxml')

    # при запуске проверяем каждый продукт, который мы получили из parse и сохраняем его
    def run(self):
        for product in self.action(self.start_url):
            self.save(product)

    # находим новые ссылки
    def action(self, url) -> dict:
        array = []
        soup = self._get_soup(self._get_response(url))
        # находим все акции
        promo = soup.find_all('input', attrs={'class': 'checkbox__control'})
        # получаем новые ссылки на акции и передаем для дальнейшей обработки
        for promo_name in promo:
            self.collect = promo_name['value']
            a = f'https://magnit.ru/promo/?geo=moskva&format[]={promo_name["value"]}'
            b = f'https://magnit.ru/promo/?geo=moskva&category[]={promo_name["value"]}'
            c = f'https://magnit.ru/promo/?geo=moskva&type[]={promo_name["value"]}'
            array.append([a, b, c])
            yield self.parse(array)

    # парсит сайт и возвращает продукты в виде словаря
    def parse(self, url) -> dict:
        for i in url:
            for j in i:
                # получаем текст нашего сайта через staticmethod
                soup = self._get_soup(self._get_response(j))
                # ищем внутри текста div с классом сatalogue__main
                catalog_main = soup.find('div', attrs={'class': 'сatalogue__main'})
                # каждый тег a с классом card-sale передаем в _get_product_data для дальнейшей обработки
                for product_tag in catalog_main.find_all('a', attrs={'class': 'card-sale'}):
                    yield self._get_product_data(product_tag)

    # составляем словарь для сохранения данных типа property
    @property
    def data_template(self):
        return {
            'url': lambda tag: urljoin(self.start_url, tag.attrs.get('href')),
            'promo_name': self.collect,
            'product_name': lambda tag: tag.find('div', attrs={'class': 'card-sale__title'}).text,
            'old_price': lambda tag: tag.find('div', attrs={'class': 'label__price_old'}).text,
            'new_price': lambda tag: tag.find('div', attrs={'class': 'label__price_new'}).text,
            'date': lambda tag: tag.find('div', attrs={'class': 'card-sale__date'}).text
        }

    # разбираем тег на составляющие
    def _get_product_data(self, product_tag: bs4.Tag) -> dict:
        data = {}
        for key, pattern in self.data_template.items():
            try:
                data[key] = pattern(product_tag)
            # лучше сохранить с некоторыми недочетами, чем не сохранять вообще
            except AttributeError:
                pass
        return data

    #  сохранение
    def save(self, data):
        collection = self.data_base[self.collect]
        collection.insert_many(data)


if __name__ == '__main__':
    load_dotenv('.env')
    data_base_url = os.getenv('DATA_BASE_URL')
    data_client = pymongo.MongoClient(data_base_url)
    url = 'https://magnit.ru/promo/?geo=moskva'
    perser = MagnitParse(url, data_client, None)
    perser.run()
