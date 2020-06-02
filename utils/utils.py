from .scraper import SanmarSpider
from scrapy.crawler import CrawlerRunner
from scrapy.signalmanager import dispatcher
from scrapy import signals
import crochet
import hashlib
import base64
import hmac
import json


crochet.setup()
runner = CrawlerRunner()

test_data = json.load(open('./utils/data.json', 'r'))


def verify_sig(signed_payload, client_secret):
    encoded_json, encoded_hmac = signed_payload.split('.')

    dc_json = base64.b64decode(encoded_json)
    signature = base64.b64decode(encoded_hmac)

    expected_sig = hmac.new(client_secret.encode(), base64.b64decode(encoded_json), hashlib.sha256).hexdigest()
    authorized = hmac.compare_digest(signature, expected_sig.encode())

    return json.loads(dc_json.decode()) if authorized else False


@crochet.wait_for(timeout=60)
def run_spider(settings):
    import_type = settings['import_type']
    is_product = import_type == 'single'

    # dispatcher.connect(_item_processed, signals.item_scraped)

    eventual = runner.crawl(
        SanmarSpider, 
        start_urls=[settings['url']], 
        output=settings['items'],
        login=settings['login'],
        is_product=is_product
    )

    return eventual


def _item_processed(item, response, spider):
    # items.append(dict(item))
    pass
