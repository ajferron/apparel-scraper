from supplier_scraper.spiders.product_spider import ProductSpider
from scrapy.crawler import CrawlerProcess

process = CrawlerProcess()

process.crawl(ProductSpider, start_urls=["https://www.sanmarcanada.com/shop-catalogue/shop-by-brand/eurospun/atc-153-vintage-thermal-long-sleeve-henley-atc8064.html"])
process.start()
