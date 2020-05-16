# -*- coding: utf-8 -*-

BOT_NAME = 'supplier_scraper'
SPIDER_MODULES = ['supplier_scraper.spiders']
NEWSPIDER_MODULE = 'supplier_scraper.spiders'
DEFAULT_ITEM_CLASS = 'supplier_scraper.items'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:7.0.1) Gecko/20100101 Firefox/7.7'

ROBOTSTXT_OBEY = True
