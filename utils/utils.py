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


class Logger:
    PURPLE = '\033[95m'
    ORANGE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def __init__(self, debug):
        self.debug = debug

    def info(self, s):
        self.log(Logger.YELLOW, f'[-] {s}')

    def success(self, s):
        self.log(Logger.GREEN, f'[+] {s}')

    def error(self, s):
        self.log(Logger.RED, f'[!] {s}')

    def log(self, c, s):
        if self.debug: print(f"{c}{s}{Logger.ENDC}")


def verify_sig(signed_payload, client_secret):
    if not signed_payload: return {}

    encoded_json, encoded_hmac = signed_payload.split('.')

    dc_json = base64.b64decode(encoded_json)
    signature = base64.b64decode(encoded_hmac)

    expected_sig = hmac.new(client_secret.encode(), base64.b64decode(encoded_json), hashlib.sha256).hexdigest()
    authorized = hmac.compare_digest(signature, expected_sig.encode())

    return json.loads(dc_json.decode()) if authorized else {}


def get_result(upload):
    result = crochet.retrieve_result(upload['thread'])

    try:
        return result.wait(0.1)

    except crochet.TimeoutError:
        upload['thread'] = result.stash()

        return False


@crochet.wait_for(timeout=60)
def run_spider(settings):
    # dispatcher.connect(_item_processed, signals.item_scraped)

    import_type = settings['import_type']
    is_product = import_type == 'single'

    return runner.crawl(
        SanmarSpider, 
        start_urls=[settings['url']], 
        output=settings['items'],
        login=settings['login'],
        is_product=is_product
    )


def _item_processed(item, response, spider):
    pass
