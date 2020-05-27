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

test_data = json.load( open('./utils/data.json', 'r') )


def verify_payload(signed_payload, client_secret):
    encoded_json, encoded_hmac = signed_payload.split('.')

    dc_json = base64.b64decode(encoded_json)
    signature = base64.b64decode(encoded_hmac)

    expected_sig = hmac.new(client_secret.encode(), base64.b64decode(encoded_json), hashlib.sha256).hexdigest()
    authorized = hmac.compare_digest(signature, expected_sig.encode())

    return json.loads(dc_json.decode()) if authorized else False


def parse_user(json):
    print('RESPONSE')
    print(json)

    token = json['access_token']
    scope = json['scope']
    user_id = json['user'].get('id')
    user_name = json['user'].get('username')
    user_email = json['user'].get('email')
    store_hash = json['context']


@crochet.wait_for(timeout=60)
def run_spider(settings):
    url = settings['url']
    items = settings['items']
    login = settings['login']

    dispatcher.connect(_item_processed, signal=signals.item_scraped)
    eventual = runner.crawl(SanmarSpider, start_urls=[url], output=items, login=login)

    return eventual


def _item_processed(item, response, spider):
    # items.append(dict(item))
    pass
