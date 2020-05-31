import scrapy
from .items import SanmarProduct


class SanmarSpider(scrapy.Spider):

    name = "products"

    custom_settings = {
        "DOWNLOAD_DELAY": 1
    }
    
    _custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "IMAGES_STORE": 'images',
        "ITEM_PIPELINES": {
            'scraper.pipelines.ProductImagePipeline': 100,
            'scraper.pipelines.JsonWriterPipeline': 200
        }
    }

    def start_requests(self):
        return [scrapy.FormRequest(
            url = "https://www.sanmarcanada.com/flashconnect/index/index/",
            callback = self.after_login,
            formdata = {
                'w3exec': 'login',
                'customerNo': self.login['id'],
                'email': self.login['email'],
                'password': self.login['pass'],
                'send': ''
            }
        )]

    def after_login(self, response):
        if 'login' in response.url:
            self.logger['error'] = 'Failed login'
            return

        return [scrapy.Request(url=url, meta={'product': self.is_product}) for url in self.start_urls]


    def parse(self, response):
        if (response.meta.get('product', False)):
            yield self.parse_product(response)

        else:
            for product in response.css('.products-grid .item'):
                name = product.css('h2 a::text').get()
                url = product.css('h2 a::attr(href)').get()

                if 'DISCONTINUED' not in name:
                    yield scrapy.Request(url=url, meta={'product': True}, callback=self.parse)


    def parse_product(self, response):
        name, sku = response.css('.product-name h1::text').get().split('.')
        desc = response.css('.short-description .std ul').get().replace("\n", "")
        imgs = response.css('#itemslider-zoom')[0]
        urls = imgs.css(".item a::attr(href)").getall()
        clrs = imgs.css('.item a::attr(title)').getall()

        clrs[0] = 'Thumbnail'
        sku = sku.replace(' ', '')

        sizes = response.css('.productgrid .header')[0].css('td::text').getall()[2:]
        prices = response.css('.productgrid .body')[0].css('.price::text').getall()
        
        product = SanmarProduct(
            name=name,
            sku=sku,
            description=desc,
            colors=clrs,
            sizes=dict(zip(sizes, map(lambda p : p.replace('$',''), prices))),
            swatch=dict(zip(clrs, urls))
        )

        self.output.append(dict(product))

        return product
