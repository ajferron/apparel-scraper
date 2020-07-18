import requests
import json

class BigCommerceStore():
    def __init__(self, owner, client_id, client_secret):
        self.store_hash = owner.store_hash
        self.access_token = owner.access_token
        self.client_secret = client_secret
        self.client_id = client_id

        self.headers = {
            'content-type': "application/json",
            'accept': "application/json",
            'x-auth-client': self.client_id,
            'x-auth-token': self.access_token
        }


    def get_categories(self):
        url = "https://api.bigcommerce.com/stores/i32da/v3/catalog/categories"

        return requests.get(url, headers=self.headers)


    def create_product(self, product):
        url = f'https://api.bigcommerce.com/stores/{self.store_hash}/v3/catalog/products'

        data = {
            'name': product['name'],
            'sku': product['sku'],
            'description': product['description'],
            'type': 'physical',
            'images': [],
            'weight': 0,
            'categories': product['categories'],
            'price': product['sizes'][0].get('price')
        }

        for i, color in enumerate(product['swatch']):
            data['images'].append({
                'description': color,
                'image_url': product['swatch'].get(color),
                'is_thumbnail': color == 'Thumbnail',
                'sort_order': i
            })

        return requests.post(url, headers=self.headers, data=json.dumps(data))


    def delete_product(self, product_id):
        url = f'https://api.bigcommerce.com/stores/{self.store_hash}/v3/catalog/products/{product_id}'

        requests.delete(url, headers=self.headers)


    def create_size_modifier(self, product_id, product):
        url = f'https://api.bigcommerce.com/stores/{self.store_hash}/v3/catalog/products/{product_id}/modifiers'
        base_price = float(product['sizes'][0].get('price'))

        data = {
            'type': 'rectangles',
            'required': True,
            'display_name': 'Size',
            'option_values': []
        }

        for variant in product['sizes']:
            data['option_values'].append({
                'is_default': False,
                'label': variant['size'],
                'adjusters': {
                    'price': {
                        'adjuster': 'relative',
                        'adjuster_value': round(float(variant['price'])-base_price, 2)
                    }
                }
        })
 
        return requests.post(url, headers=self.headers, data=json.dumps(data))


    def create_color_modifier(self, product_id, product):
        url = f'https://api.bigcommerce.com/stores/{self.store_hash}/v3/catalog/products/{product_id}/modifiers'

        data = {
            "type": "swatch",
            "required": True,
            "display_name": "Color",
            "option_values": []
        }
        
        adjusters = []

        for i, color in enumerate(product['swatch']):
            if color != 'Thumbnail':
                image_url = {"image_url": product['swatch'].get(color)}

                adjusters.append({"adjusters": image_url})

                data['option_values'].append({
                    "sort_order": i,
                    "is_default": False,
                    "label": color,
                    "adjusters": image_url,
                    "value_data": image_url
                })
        
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        
        return {
            'response': response,
            'adjusters': adjusters
        }


    def update_modifier(self, product_id, modifier_id, val_id, adjuster):
        url = f'https://api.bigcommerce.com/stores/{self.store_hash}/v3/catalog/products/{product_id}/modifiers/{modifier_id}/values/{val_id}'
        
        return requests.put(url, headers=self.headers, data=json.dumps(adjuster))
