import scrapy
from scrapy.pipelines.images import ImagesPipeline

class ProductImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        urls = item['image_urls']
        colors = item['colors']
        idx = list(range(len(urls)))

        for url, clr, i in zip(urls, colors, idx):
            yield scrapy.Request(url, meta={'sku': item['sku'], 'color': clr, 'num': i})

    def file_path(self, request, response=None, info=None):
        sku = request.meta['sku'].lower()
        clr = request.meta['color'].lower().replace(' ', '')
        ext = request.url.split('.')[-1]
        i = request.meta['num']
        
        return f"{sku}-{clr if (i != 0) else 'main'}.{ext}"
