import scrapy
from ..items import ProductItem

# php -S localhost:8080
# scrapy crawl products
# scrapy shell -s USER_AGENT='custom user agent' "http://localhost:8080/index.html"

class ProductSpider(scrapy.Spider):
    name = "products"

    custom_settings = {
        "ITEM_PIPELINES": {'supplier_scraper.pipelines.ProductImagePipeline': 1},
        "IMAGES_STORE": 'images',
        "DOWNLOAD_DELAY": 1
    }

    def parse(self, response):
        name = response.css('.product-name h1::text').get()
        desc = response.css('.short-description .std ul').get().replace("\n", "")
        imgs = response.css('#itemslider-zoom')[0]
        urls = imgs.css(".item a::attr(href)").getall()
        clrs = imgs.css('.item a::attr(title)').getall()
        sku = name.split('.')[1].replace(' ', '')

        return ProductItem(name=name, sku=sku, description=desc, colors=clrs, image_urls=urls)
