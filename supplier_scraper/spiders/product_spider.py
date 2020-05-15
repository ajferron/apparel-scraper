import scrapy

# php -S localhost:8080
# scrapy crawl products
# scrapy shell "http://localhost:8080/index.html"

class ProductSpider(scrapy.Spider):
    name = "products"

    def parse(self, response):
        # print(response.url)
        # print(response.body)
        # response.css('.short-description .std li::text').getall()
        filename = 'product.txt'
        with open(filename, 'wb') as f:
            f.write(response.css('.short-description'))