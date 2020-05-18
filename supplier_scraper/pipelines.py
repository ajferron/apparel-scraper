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
        i = request.meta['num']
        sku = request.meta['sku'].lower()
        ext = request.url.split('.')[-1]
        clr = request.meta['color'].lower()

        if (request.meta['num'] == 0):
            return f"{sku}-thumnail.{ext}"
        else:
            color = ''.join(map(lambda l : '' if l in '/ ' else l, clr))
            return f"{sku}-{color}.{ext}"
