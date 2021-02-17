import json
import scrapy
from ..items import InstaFollowing


class InstagramSpider(scrapy.Spider):
    name = "instagram"
    allowed_domains = ["www.instagram.com"]
    start_urls = ["https://www.instagram.com/"]
    login_url = "https://www.instagram.com/accounts/login/ajax/"
    api_url = "/graphql/query/"
    query_hash = {
        'following': '3dec7e2c57367ef3da3d987d89f9dbc8',
    }

    def __init__(self, id_user, login, password, *args, **kwargs):
        self.id_user = id_user
        self.name_user_1 = 'ilianiyazov'
        self.name_user_2 = 'zapreshonka'
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
                yield response.follow(f"/{self.name_user_1}/", callback=self.user_parse)

    def user_parse(self, response):
        tag = self.js_data_extract(response)["entry_data"]["ProfilePage"][0]["graphql"]["user"]
        self.id_user = tag["id"]
        if tag:
            variables = {
                "id": self.id_user,
                "include_reel": True,
                'fetch_mutual': False,
                'first': 100,
            }

            url = f'{self.api_url}?query_hash={self.query_hash["following"]}&variables={json.dumps(variables)}'
            yield response.follow(
                url,
                callback=self.user_api_parse,
            )

    def user_api_parse(self, response):
        yield from self.get_user(response.json(), response)

    def get_user(self, tag, response):
        if tag:
            variables = {
                "id": self.id_user,
                "include_reel": True,
                'fetch_mutual': False,
                'first': 100,
                "after": tag['data']['user']['edge_follow']['page_info']["end_cursor"],
            }

            url = f'{self.api_url}?query_hash={self.query_hash["following"]}&variables={json.dumps(variables)}'
            yield response.follow(
                url,
                callback=self.user_api_parse,
            )

        yield from self.get_post_following(self.name_user_2, tag['data']['user']['edge_follow']["edges"], response)


    def get_post_following(self, user_2, edges, response):
        for node in edges:
            if node['node']['username'] == user_2:
                yield InstaFollowing(data='друг нашелся')
            else:
                yield response.follow(f"/{node['node']['username']}/", callback=self.user_parse)

    @staticmethod
    def js_data_extract(response):
        script = response.xpath('//script[contains(text(), "window._sharedData =")]/text()').get()
        return json.loads(script.replace("window._sharedData =", "")[:-1])
