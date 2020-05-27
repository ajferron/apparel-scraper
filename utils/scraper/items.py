import scrapy

class SanmarProduct(scrapy.Item):
    sku = scrapy.Field()
    name = scrapy.Field()
    colors = scrapy.Field()
    sizes = scrapy.Field()
    swatch = scrapy.Field()
    description = scrapy.Field()
    images = scrapy.Field()
    image_urls = scrapy.Field()
