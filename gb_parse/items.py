# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
# тут храним все data которые должны быть

import scrapy


class GbParseItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass



class Insta(scrapy.Item):
    _id = scrapy.Field()
    date_parse = scrapy.Field()
    data = scrapy.Field()
    img = scrapy.Field()


class InstaTag(Insta):
    pass


class InstaPost(Insta):
    pass


class InstaUser(Insta):
    pass


# кто подписан на него
class InstaFollowers(Insta):
    pass


# на кого подписан
class InstaFollowing(Insta):
    pass
