import os
from dotenv import load_dotenv
import requests
import bs4
from urllib.parse import urljoin
import datebase


class GbParse:
    def __init__(self, start_url, db):
        self.start_url = start_url
        self.done_url = set()
        self.tasks = [self.parse_task(self.start_url, self.pag_parse)]
        self.done_url.add(self.start_url)
        self.db = db

    # проверка url что он работает
    @staticmethod
    def _get_response(*args, **kwargs):
        # todo обработка ошибок
        return requests.get(*args, **kwargs)

    # парсим наш сайт целиком
    def _get_soup(self, *args, **kwargs):
        response = self._get_response(*args, **kwargs)
        return bs4.BeautifulSoup(response.text, 'lxml')

    # некие элементы к кторым мы будем обращаться
    def parse_task(self, url, callback):
        def task():
            soup = self._get_soup(url)
            return callback(url, soup)

        return task

    def run(self):
        for task in self.tasks:
            result = task()
            if result:
                self.save(result)

    # парсим каждую страницу (пагинация)
    def pag_parse(self, url, soup):
        self.create_parse_tasks(
            url, soup.find("ul", attrs={"class": "gb__pagination"}).find_all("a"), self.pag_parse
        )

        self.create_parse_tasks(
            url,
            soup.find('div', attrs={'class': 'post-items-wrapper'}).find_all("a", attrs={"class": "post-item__title"}),
            self.post_parse
        )

    def create_parse_tasks(self, url, tag_list, callback):
        for a_tag in tag_list:
            a_url = urljoin(url, a_tag.get('href'))
            if a_url not in self.done_url:
                task = self.parse_task(a_url, callback)
                self.tasks.append(task)
                self.done_url.add(a_url)

    def parse_comment(self, url):
        response = requests.get(url)
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        soup_2 = soup.find('div', attrs={'class': 'referrals-social-buttons-small-wrapper'})
        s = soup_2['data-minifiable-id']

        url_new = f'https://geekbrains.ru/api/v2/comments?commentable_type=Post&commentable_id={s}&order=desc'
        response = requests.get(url_new)
        data = response.json()
        array = {}
        if len(data) == 0:
            return 'нету'
        else:
            for i in data:
                data_new = i
                array.update({data_new['comment']['user']['full_name']: data_new['comment']['body']})
        return self.test(array)

    def test(self, data):
        for key, value in data.items():
            return f'{key}-{value}'

    # парсим каждый пост
    def post_parse(self, url, soup: bs4.BeautifulSoup) -> dict:
        author_name_tag = soup.find("div", attrs={"itemprop": "author"})
        data = {
            "post_data": {
                "url": url,
                "title": soup.find("h1", attrs={"class": "blogpost-title"}).text,
            },
            "author": {
                "url": urljoin(url, author_name_tag.parent.get("href")),
                "name": author_name_tag.text,
            },
            "tags": [
                {
                    "name": tag.text,
                    "url": urljoin(url, tag.get("href")),
                }
                for tag in soup.find_all("a", attrs={"class": "small"})
            ],
            "comment": [
                {
                    "url": url,
                    "name": self.parse_comment(url)
                }
            ]
        }
        return data

    # сохранение
    def save(self, data):
        self.db.create_post(data)


if __name__ == '__main__':
    load_dotenv('.env')
    db = datebase.Databases(os.getenv('SQL_DB_URL'))
    parse = GbParse('https://geekbrains.ru/posts', db)
    parse.run()
