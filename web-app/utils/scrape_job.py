from .scraper import Scraper, SanmarScraper, TrimarkScraper, DebcoScraper, TechnoScraper
from .utils import Logger
from datetime import datetime
from uuid import uuid4
import requests
import json


class ScrapeJob():
    scrapers = {
        'sanmar': SanmarScraper,
        'trimark': TrimarkScraper,
        'debco': DebcoScraper,
        'technosport': TechnoScraper
    }


    def __init__(self, options):
        self.job_id = str(uuid4())

        self._url = options.get('url', '')
        self._api = options.get('api', '')
        self._job_type = options.get('job_type', '')
        self._supplier = options.get('supplier', '')
        self._settings = options.get('settings')
        self._status = options.get('status', '')
        self._logger = options.get('logger')

        self.scraper = ScrapeJob.scrapers.get(self._supplier, lambda _ : None)({})

        if (not self.scraper):
            raise TypeError('Could not import from the given URL')

        self.scraper.job_id = self.job_id
        self.scraper.urls = self.urls
        self.scraper.login_details = self.settings

        self._logger.success('Started new Scrape Job')


    @property
    def urls(self):
        if type(self._url) == str:
            urls = { # lamda prevents grid_parse() on declaration
                'single': lambda url : [url],
                'page': lambda url : self.scraper.grid_parse(url)

            }[self._job_type](self._url)

            convert = lambda u : {'url':u, 'id':str(uuid4())}

            self._url = list(map(convert, urls))

        return self._url


    @property
    def settings(self):
        obj = {
            'sanmar': self._settings.sanmar_config,
            'trimark': self._settings.trimark_config,
            'debco': self._settings.debco_config,
            'technosport': self._settings.technosport_config
        }

        return json.loads(obj.get(self._supplier, {}))


    def run(self):
        self._logger.info('Posting Scrape Job to API...')

        res = requests.post(
            url=f'{self._api}/feed', 
            data=self.scraper.json(),
            headers={
                'Content-Type': 'application/json'
            }
        )

        self._logger.success(f'Posted Scrape Job to API')

        return res.json()


    def json(self):
        # Can be used to instantiate a new ScrapeJob 
        # Needs settings, logger, and api url from app

        return json.dumps({
            'urls': self._url,
            'job_type': self._job_type,
            'supplier': self._supplier,
            'name': datetime.now().strftime('%B %d, %Y %I:%M:%S %p')
        })
