from .scraper import Scraper
import json


class SanmarScraper(Scraper):
    def grid_parse(self, url):
        return [url]


    @property
    def login_details(self):
        if self._user_settings == {}:
            raise KeyError(f'Please add login credentials for Sanmar')

        return {
            'form_url': 'https://www.sanmarcanada.com/customer/account/login',
            'submit_btn': '#send2',
            'fields': {
                '#customerNo': self._user_settings.get('user_id', ''),
                '#email': self._user_settings.get('email', ''),
                '#pass': self._user_settings.get('password', '')
            }
        }


    @login_details.setter
    def login_details(self, settings):
        self._user_settings = settings


    @property
    def extractor(self):
        return (
            """ 
                $ => {
                    let [name, sku] = $('.product-name h1').text().split('.').map(s => s.trim())
                    let desc = $('.short-description ul').html()
                    let swatch = $('#itemslider-zoom').first().find('.item a').map((i, e) => ({color: $(e).attr('title'), url: $(e).attr('href')})).get()
                    let sizes = $('.productgrid .header').first().find('td:not(".left")').toArray().map(e => $(e).text())
                    let prices = $('.productgrid .body').first().find('.price').toArray().map(e => $(e).text().replace('$',''))

                    sku.replace(' ', '')
                    swatch[0].color = 'Thumbnail'
                    sizes = sizes.map((e, i) => ({label: e, price: prices[i]}))

                    return {name, sku, desc, swatch, sizes}
                }
            """
        )