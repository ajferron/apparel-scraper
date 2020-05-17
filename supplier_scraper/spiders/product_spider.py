import scrapy
from ..items import ProductItem

# php -S localhost:8080
# scrapy crawl products
# scrapy shell -s USER_AGENT='custom user agent' "http://localhost:8080/index.html"

sanmar_login = {
    'w3exec': 'login', 
    'customerNo': '27539',
    'email': 'email',
    'password': 'pass', 
    'send': ''
}

class ProductSpider(scrapy.Spider):
    name = "products"

    custom_settings = {
        "IMAGES_STORE": 'images',
        "DOWNLOAD_DELAY": 1,
        "ITEM_PIPELINES": {
            'supplier_scraper.pipelines.ProductImagePipeline': 100

        }
    }

    def start_requests(self):
        return [scrapy.FormRequest(
            url = "https://www.sanmarcanada.com/flashconnect/index/index/",
            formdata = sanmar_login,
            callback = self.after_login
        )]


    def after_login(self, response):
        if 'login' in response.url:
            self.logger.error("[!] LOGIN FAILED")
            return
        
        return [scrapy.Request(url=url, meta={'product': False}) for url in self.start_urls]

    def parse(self, response):
        name = response.css('.product-name h1::text').get()
        desc = response.css('.short-description .std ul').get().replace("\n", "")
        imgs = response.css('#itemslider-zoom')[0]
        urls = imgs.css(".item a::attr(href)").getall()
        clrs = imgs.css('.item a::attr(title)').getall()
        sku = name.split('.')[1].replace(' ', '').lower()

        return ProductItem(name=name, sku=sku, description=desc, colors=clrs, image_urls=urls)
