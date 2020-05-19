import scrapy
import json
from datetime import datetime
from webdav.client import Client
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
        clr = request.meta['color'].lower()
        ext = request.url.split('.')[-1]

        if (request.meta['num'] == 0):
            return f"{sku}-thumbnail.{ext}"
        else:
            color = ''.join(map(lambda l : '' if l in '/ ' else l, clr))
            return f"{sku}-{color}.{ext}"



class JsonWriterPipeline():

    def open_spider(self, spider):
        self.json = {'items': []}
        date = datetime.now().strftime("%d-%m-%Y_%I:%M:%S%p")
        self.file = open(f'Products_{date}.json', 'w')


    def close_spider(self, spider):
        self.file.write(json.dumps(self.json))
        self.file.close()


    def process_item(self, item, spider):
        urls = map(lambda img : img['path'], item['images'])
        swatches = zip(item['colors'], [url for url in urls])
        item['swatches'] = [{'color': clr, 'image': url} for clr, url in swatches]

        del item['colors']
        del item['images']
        del item['image_urls']

        self.json['items'].append(dict(item))

        return item



class WebDavPipeline():

    def open_spider(self, spider):
        self.client = Client({
            'webdav_hostname': "https://www.adventnorthcanada.com/dav",
            'webdav_root': "dav",
            'webdav_login': "alvin@adventnorthcanada.com",
            'webdav_password': "30d4ffdaa63d30b2aa484f99f5a9e5d126e12d15e29276dd6dca45b9dd80eec1"
        })

        Client({'webdav_hostname': "https://www.adventnorthcanada.com/",'webdav_root': "dav",'webdav_login': "alvin@adventnorthcanada.com",'webdav_password': "30d4ffdaa63d30b2aa484f99f5a9e5d126e12d15e29276dd6dca45b9dd80eec1"})
        
        self.client.verify = False

    def process_item(self, item, spider):
        for swatch in item['swatches']:
            self.client.upload_sync(remote_path=f'/dav/product_images/import/{swatch["image"]}', local_path=f'images/{swatch["image"]}')
            client.upload_sync(remote_path='/dav/product_images/import/l4022-black.jpg', local_path='images/l4022-black.jpg')

        return item
