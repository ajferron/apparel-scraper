from flask import Flask
from api import api_bp
import os


app = Flask(__name__)

app.config['APP_CLIENT_ID'] = os.getenv('APP_CLIENT_ID')
app.config['APP_CLIENT_SECRET'] = os.getenv('APP_CLIENT_SECRET')


app.register_blueprint(api_bp)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))

    app.run(host='0.0.0.0', port=port)
