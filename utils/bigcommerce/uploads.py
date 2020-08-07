import requests
import json


class ProductUpload():
    def __init__(self, store, product):
        self.product = product
        self.store = store

        self.headers = self.store.headers


    def _request(self, method, url, data):
        r = requests.request(method, url, headers=self.headers, data=data)

        return { # Might want to create a Response class
            'status_code': r.status_code,
            'url': r.json().get('data', {}).get('custom_url', {}).get('url', ''),
            'values': r.json().get('data', {}).get('option_values', []),
            'id': r.json().get('data', {}).get('id', '')
        }


    def _post(self, endpoint, data, **kwargs):
        url = {
            'product': f"https://api.bigcommerce.com/stores/{self.store.store_hash}/v3/catalog/products",
            'modifier': f"https://api.bigcommerce.com/stores/{self.store.store_hash}/v3/catalog/products/{self.product.id}/modifiers",
        }.get(endpoint)

        return self._request('POST', url, data)


    def _put(self, endpoint, data, **kwargs):
        url = {
            'update-modifier': f"https://api.bigcommerce.com/stores/{self.store.store_hash}/v3/catalog/products/{self.product.id}/modifiers/{kwargs.get('m_id', '')}/values/{kwargs.get('v_id', '')}"
        }.get(endpoint)

        return self._request('PUT', url, data)


    def post_product(self):
        response = self._post('product', self.product.json)

        if response.get('status_code') == 200:
            self.product.id = response.get('id')

        return response


    def post_modifiers(self):
        for m in self.product.modifiers:
            modifier = self.product.modifiers[m]
            response = self._post('modifier', modifier.json)

            if response.get('status_code') == 200:
                modifier_value_ids = map(lambda v : v['id'], response.get('values'))
                modifier_adjusters = zip(modifier_value_ids, modifier.adjusters)

                modifier.id = response.get('id')
                modifier.adjusters = modifier_adjusters

            yield response


    def update_modifier(self, m):
        modifier = self.product.modifiers[m]

        for i, adjuster in modifier.adjusters:
            adjuster = json.dumps({'adjusters': adjuster})

            yield self._put('update-modifier', adjuster, m_id=modifier.id, v_id=i)
