from abc import ABC, abstractmethod
from uuid import uuid4
import json
import re


class Scraper(ABC):
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'

    def __init__(self, options):
        self._job_id = options.get('job_id', str(uuid4()))
        self._urls = options.get('urls', [])
        self._user_settings = options.get('login')


    @property
    def job_id(self):
        return self._job_id


    @job_id.setter
    def job_id(self, job_id):
        self._job_id = job_id


    @property
    def urls(self):
        # https://github.com/django/django/blob/stable/1.3.x/django/core/validators.py#L45

        regex = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?(?:/?|[/?]\S+)$', 
            re.IGNORECASE
        )

        urls = filter(lambda url : re.match(regex, url.get('url', '')), self._urls)

        return list(urls)


    @urls.setter
    def urls(self, urls):
        self._urls = urls


    @abstractmethod
    def grid_parse(self, url):
        # Use custom extractor and request to API to scrape URLs from url
        # Extractor will yield res = {urls: ['', '', ...]}
        # grid_parse(...) will yield res['urls']

        pass


    @property
    @abstractmethod
    def login_details(self):
        # Specifies the login form, fields, credentials.
        # Login form is submitted before scraping

        # ex.
        # {
        #     'form_url': 'https://www.website.com//login',
        #     'submit_btn': '#login',
        #     'fields': {
        #         '#customerNo': '12345',
        #         '#email': 'example@yea.com',
        #         '#pass': 'abc'
        #     }
        # }

        pass


    @login_details.setter
    def login_details(self, settings):
        self._user_settings = settings


    @property
    @abstractmethod
    def extractor(self):
        # A JS function that defines which content to extract from the urls
        # Yields {name, sku, desc, swatch, sizes} for import_review.html

        # ex. "($) => ({title: $('.product-name h1').text()})"

        pass


    def json(self):
        return json.dumps({
            'job_id': self.job_id,
            'urls': self.urls,
            'extractor': self.extractor,
            'userAgent': self.user_agent,
            'login': self.login_details,
        }, indent=2)
