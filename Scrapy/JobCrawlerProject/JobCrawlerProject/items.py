# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class JobcrawlerprojectItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class JobItem(scrapy.Item):
    name = scrapy.Field()
    link = scrapy.Field()
    boss_name = scrapy.Field()
    boss_title = scrapy.Field()
    salary = scrapy.Field()
    skills = scrapy.Field()
    experience = scrapy.Field()
    degree = scrapy.Field()
    city = scrapy.Field()
    area = scrapy.Field()
    address = scrapy.Field()
    company = scrapy.Field()
    scale = scrapy.Field()
    welfare = scrapy.Field()
    description = scrapy.Field()
    address_detail = scrapy.Field()

