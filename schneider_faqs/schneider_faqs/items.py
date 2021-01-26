# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SchneiderFaqsItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()  # string
    file_name = scrapy.Field()
    download_link = scrapy.Field()
    detail_page = scrapy.Field()
