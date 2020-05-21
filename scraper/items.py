# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class ProductItem(scrapy.Item):
    sku = scrapy.Field()
    name = scrapy.Field()
    colors = scrapy.Field()
    sizes = scrapy.Field()
    swatches = scrapy.Field()
    description = scrapy.Field()
    images = scrapy.Field()
    image_urls = scrapy.Field()
