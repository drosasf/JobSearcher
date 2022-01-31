# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class SiteScraperItem(Item):
    # define the fields for your item here like:
    job = Field()
    company = Field()
    location = Field()
    date = Field()
    link = Field()
    site = Field()
    opened = Field()
    pass
