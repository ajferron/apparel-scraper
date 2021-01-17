import json


class Modifier():
    def __init__(self, name, mod_type, required=True):
        self.name = name 
        self.type = mod_type 
        self.required = required

        self.adjusters = []
        self.options = []


    @property
    def json(self):
        import json

        return json.dumps({
            'display_name': self.name,
            'type': self.type,
            'required': self.required,
            'option_values': self.options
        })
