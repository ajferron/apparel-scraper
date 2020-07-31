from .modifier import Modifier


class Product():
    def __init__(self, product):
        self.sku = product.get('sku', '')
        self.name = product.get('name', '')
        self.description = product.get('description', '')
        self.categories = product.get('categories', [])
        self.swatch = product.get('swatch', [{}])
        self.sizes = product.get('sizes', [{}])

        self.price = float(self.sizes[0].get('price', -1))

        self.modifiers = {}
        self.id = -1

        self._images = []


    @property
    def images(self):
        self._images = []

        for i, color in enumerate(self.swatch):
            self._images.append({
                'description': color,
                'image_url': self.swatch.get(color),
                'is_thumbnail': color == 'Thumbnail',
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
