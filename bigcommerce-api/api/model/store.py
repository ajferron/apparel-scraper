from .upload import ProductUpload
from .product import Product
from .modifier import Modifier
import requests
import json


class BigCommerceStore():
    def __init__(self, config):
        self.store_hash = config.get('store_hash', 0)
        self.access_token = config.get('access_token', 0)
        self.client_secret = config.get('client_secret', '')
        self.client_id = config.get('client_id', '')

        # Test values and throw errors accordingly


    def create_product(self, data):
        p = Product(data)

        p.modifiers['size'] = self._size_modifier(p.sizes, p.price)
        p.modifiers['color'] = self._color_modifier(p.swatch)

        # Put this in a thread

        return self._upload_product(p)


    def _upload_product(self, product):
        upload = ProductUpload(self, product)

        # Throw errors instead of returning response
        # Or return dicts? This will be in a thread

        response = upload.post_product()

        if response.get('status_code') != 200:
            return response

        url = response.get('url')

        for response in upload.post_modifiers():
            if response.get('status_code') != 200:
                return response

        for response in upload.update_modifier('color'):
            if response.get('status_code') != 200:
                return response

        return url


    def _size_modifier(self, sizes, base_price):
        modifier = Modifier('Size', 'rectangles')

        for variant in sizes:
            price = float(variant.get('price', 0))

            modifier.adjusters.append({
                'price': {
                    'adjuster': 'relative',
                    'adjuster_value': round(price-base_price, 2)
                }
            })

            modifier.options.append({
                'is_default': False,
                'label': variant.get('label', '-'),
                'adjusters': modifier.adjusters[-1]
            })

        return modifier


    def _color_modifier(self, swatch):
        modifier = Modifier('Color', 'swatch')

        for i, swatch in enumerate(swatch):
            if swatch.get('color') != 'Thumbnail':
                modifier.adjusters.append({
                    'image_url': swatch.get('url')
                })

                modifier.options.append({
                    'sort_order': i,
                    'is_default': False,
                    'label': swatch.get('color'),
                    'adjusters': modifier.adjusters[-1],
                    'value_data': modifier.adjusters[-1]
                })

        return modifier


    def get_categories(self):
        url = f"https://api.bigcommerce.com/stores/{self.store_hash}/v3/catalog/categories"

        return requests.get(url, headers=self.headers)


    def delete_product(self, product_id):
        url = f'https://api.bigcommerce.com/stores/{self.store_hash}/v3/catalog/products/{product_id}'

        return requests.delete(url, headers=self.headers)
