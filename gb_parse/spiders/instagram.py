import json
import scrapy
import datetime
from ..items import InstaFollowers, InstaFollowing


class InstagramSpider(scrapy.Spider):
    name = "instagram"
    allowed_domains = ["www.instagram.com"]
    start_urls = ["https://www.instagram.com/"]
    login_url = "https://www.instagram.com/accounts/login/ajax/"
    api_url = "/graphql/query/"
    query_hash = {
        'followers': '5aefa9893005572d237da5068082d8d5',
        'following': '3dec7e2c57367ef3da3d987d89f9dbc8',
    }

    def __init__(self, id_user, login, password, *args, **kwargs):
        self.id = id_user
        self.names = ['ilianiyazov']
        self.login = login
        self.enc_passwd = password
        super().__init__(*args, **kwargs)

    def parse(self, response, **kwargs):
        try:
            js_data = self.js_data_extract(response)
            yield scrapy.FormRequest(
                self.login_url,
                method="POST",
                callback=self.parse,
                formdata={
                    "username": self.login,
                    "enc_password": self.enc_passwd,
                },
                headers={"X-CSRFToken": js_data["config"]["csrf_token"]},
            )
        except AttributeError:
            if response.json().get("authenticated"):
                for name in self.names:
                    yield response.follow(f"/{name}/", callback=self.user_parse)

    def user_parse(self, response):
        tag = self.js_data_extract(response)['config']['viewer']
        self.id = tag["id"]
        if tag:
            variables = {
                "id": self.id,
                "include_reel": True,
                'fetch_mutual': False,
                'first': 50,
            }
            url = f'{self.api_url}?query_hash={self.query_hash["followers"]}&variables={json.dumps(variables)}'
            yield response.follow(
                url,
                callback=self.user_api_parse,
            )

    def user_api_parse(self, response):
        yield from self.get_user_followers(response.json(), response)
        yield from self.get_user_following(response.json(), response)

    def get_user(self, tag):
        if tag:
            variables = {
                "id": self.id,
                "include_reel": True,
                'fetch_mutual': False,
                'first': 50,
                "after": tag['data']['user']['edge_followed_by']['page_info']["end_cursor"],
            }
            yield json.dumps(variables)

    def get_user_followers(self, tag, response):
        url = f'{self.api_url}?query_hash={self.query_hash["followers"]}&variables={self.get_user(tag["data"]["user"]["edge_followed_by"])}'
        yield response.follow(
            url,
            callback=self.user_api_parse,
        )

        yield from self.get_post_follows(tag['data']['user']['edge_followed_by']["edges"])

    def get_user_following(self, tag, response):
        url = f'{self.api_url}?query_hash={self.query_hash["following"]}&variables={self.get_user(tag["data"]["user"]["edge_followed_by"])}'
        yield response.follow(
            url,
            callback=self.user_api_parse,
        )

        yield from self.get_post_following(tag['data']['user']['edge_followed_by']["edges"])

    @staticmethod
    def get_post_follows(edges):
        for node in edges:
            yield InstaFollowers(date_parse=datetime.datetime.utcnow(), data=node["node"])

    @staticmethod
    def get_post_following(edges):
        for node in edges:
            yield InstaFollowing(date_parse=datetime.datetime.utcnow(), data=node["node"])

    def js_data_extract(self, response):
        script = response.xpath('//script[contains(text(), "window._sharedData =")]/text()').get()
        return json.loads(script.replace("window._sharedData =", "")[:-1])
