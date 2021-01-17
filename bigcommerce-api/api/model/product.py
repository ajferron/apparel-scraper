
from .modifier import Modifier


class Product():
    def __init__(self, product):
        self.sku = product.get('sku', '')
        self.name = product.get('name', '')
        self.description = product.get('description', '')
        self.categories = product.get('categories', [])
        self.swatch = product.get('swatch', [{}])
        self.sizes = product.get('sizes', [{}])

        self.price = float(self.sizes[0].get('price', 0))

        self.modifiers = {}
        self.id = -1

        self._images = []


    @property
    def images(self):
        for i, swatch in enumerate(self.swatch):
            self._images.append({
                'description': swatch.get('color', '-'),
                'image_url': swatch.get('url', '-'),
                'is_thumbnail': swatch.get('url') == 'Thumbnail',
                'sort_order': i
            })

        return self._images


    @property
    def json(self):
        import json

        return json.dumps({
            'name': self.name,
            'sku': self.sku,
            'description': self.description,
            'categories': self.categories,
            'images': self.images,
            'price': self.price,
            'type': 'physical',
            'weight': 0
        })
