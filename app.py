from flask import Flask, request, session, render_template, make_response, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from scrapy.crawler import CrawlerRunner
from scrapy.signalmanager import dispatcher
from scrapy import signals
from scraper import ProductSpider
from uuid import uuid4
import hmac, hashlib, base64
import dotenv
import crochet
import requests
import json
import os


app = Flask(__name__)

if os.path.exists('.env'):
    dotenv.load_dotenv('.env')

app.config['APP_CLIENT_ID'] = os.getenv('APP_CLIENT_ID')
app.config['APP_CLIENT_SECRET'] = os.getenv('APP_CLIENT_SECRET')
app.config['SESSION_SECRET'] = os.getenv('SESSION_SECRET')
app.config['SQLALCHEMY_DATABASE_URI'] = ''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


def verify_payload(signed_payload, client_secret):
    encoded_json, encoded_hmac = signed_payload.split('.')
    
    dc_json = base64.b64decode(encoded_json)
    signature = base64.b64decode(encoded_hmac)
    
    expected_sig = hmac.new(client_secret.encode(), base64.b64decode(encoded_json), hashlib.sha256).hexdigest()
    authorized = hmac.compare_digest(signature, expected_sig.encode())

    return json.loads(dc_json.decode()) if authorized else False


def _item_processed(item, response, spider):
    # items.append(dict(item))
    pass


def client_id():
    return app.config['APP_CLIENT_ID']


def client_secret():
    return app.config['APP_CLIENT_SECRET']


def session_secret():
    return app.config['SESSION_SECRET']



app.secret_key = session_secret()

runner = CrawlerRunner()
db = SQLAlchemy(app)

crochet.setup()


def parse_user(json):
    print('RESPONSE')
    print(json)

    token = json['access_token']
    scope = json['scope']
    user_id = json['user'].get('id')
    user_name = json['user'].get('username')
    user_email = json['user'].get('email')
    store_hash = json['context']


@app.route('/')
def index():
    payload = request.args.get('signed_payload', '')
    data = verify_payload(payload, client_secret())
    session['data'] = data

    return render_template('index.html')



@app.route('/auth')
def auth():
    session['temp_auth'] = {
        'code': request.args.get('code', ''),
        'scope': request.args.get('scope', ''),
        'context': request.args.get('context', '')
    }

    return render_template('auth.html')



@app.route('/uninstall')
def uninstall():
    return render_template('uninstall.html')



@app.route('/submit_import', methods=['POST'])
def submit_import():
    session['scrape'] = {
        'url': request.form['url'],
        'import_type': request.form['import-type'],
        'status': 'Connecting...',
        'items': [],
        'login': {
            'id': request.form['id'],
            'email': request.form['email'],
            'pass': request.form['password'],
        }
    }

    return render_template('wait.html')



@app.route('/authorize', methods=['POST'])
def authorize():
    url = 'https://login.bigcommerce.com/oauth2/token'
    headers = {'content-type': 'application/x-www-form-urlencoded'}

    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': session['temp_auth'].get('code', ''),
        'scope': session['temp_auth'].get('scope', ''),
        'context': session['temp_auth'].get('context', ''),
        'grant_type': 'authorization_code',
        'redirect_uri': 'http://127.0.0.1:5000/auth'
    }

    session.pop('temp_auth', None)

    response = requests.post(url, headers=headers, data=data).json()

    if 'error' in response:
        return render_template('error.html', message='Unable to authorize, try again later.')
    else:
        parse_user(response)

    return render_template('index.html')



@app.route("/icons/<file_name>.svg")
def get_icon(file_name):
    response = make_response(render_template(f'icons/{file_name}.svg'))
    response.mimetype = 'image/svg+xml'
    
    return response



@app.route("/scrape")
def scrape():
    scraper_settings = session['scrape']

    scrape_with_crochet(scraper_settings)

    return json.dumps(scraper_settings['items'])



@crochet.wait_for(timeout=60)
def scrape_with_crochet(settings):
    url = settings['url']
    items = settings['items']
    login = settings['login']

    dispatcher.connect(_item_processed, signal=signals.item_scraped)
    eventual = runner.crawl(ProductSpider, start_urls=[url], output=items, login=login)

    return eventual



if __name__ == '__main__':
    app.debug = True
    app.run()
