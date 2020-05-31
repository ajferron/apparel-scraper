from flask import Flask, request, session, render_template, make_response, jsonify, url_for
from utils import BigCommerceStore, verify_sig, test_data, run_spider
from flask_sqlalchemy import SQLAlchemy
import dotenv
import requests
import json
import os

DEBUG = False

app = Flask(__name__)

if os.path.exists('.env'):
    dotenv.load_dotenv('.env')

app.config['APP_CLIENT_ID'] = os.getenv('APP_CLIENT_ID')
app.config['APP_CLIENT_SECRET'] = os.getenv('APP_CLIENT_SECRET')
app.config['SESSION_SECRET'] = os.getenv('SESSION_SECRET')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


def client_id():
    return app.config['APP_CLIENT_ID']


def client_secret():
    return app.config['APP_CLIENT_SECRET']


def session_secret():
    return app.config['SESSION_SECRET']



app.secret_key = session_secret()

db = SQLAlchemy(app)



class StoreOwner(db.Model):
    # in python env...
    # from app import db
    # db.createall()

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    store_hash = db.Column(db.String(24), unique=True)
    access_token = db.Column(db.String(64), unique=True)
    scope = db.Column(db.String(), unique=False)
    username = db.Column(db.String(), unique=True)
    email = db.Column(db.String(), unique=True)
     
    def __init__(self, data):
        self.access_token = data['access_token']
        self.store_hash = data['context'].split('/')[1]
        self.username = data['user'].get('username')
        self.email = data['user'].get('email')
        self.id = data['user'].get('id')
        self.scope = data['scope']



@app.route('/')
def index():
    payload = request.args.get('signed_payload', '')

    session['bc_data'] = verify_sig(payload, client_secret()) if payload else {}

    return render_template('index.html')



@app.route('/auth')
def auth():
    session['temp_auth'] = {
        'code': request.args.get('code', ''),
        'scope': request.args.get('scope', ''),
        'context': request.args.get('context', '')
    }

    return render_template('auth.html')



@app.route('/uninstall/')
def uninstall():
    payload = request.args.get('signed_payload', '')
    bc_data = verify_sig(payload, client_secret()) if payload else {}

    if bc_data:
        user_id = bc_data['user'].get('id')
        store_owner = StoreOwner.query.get(int(user_id))

        if store_owner is not None:
            db.session.delete(store_owner)
            db.session.commit()

    return render_template('uninstall.html')



@app.route('/authorize', methods=['POST'])
def authorize():
    url = 'https://login.bigcommerce.com/oauth2/token'
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    redirect = {
        'prod': 'https://apparel-scraper.herokuapp.com/auth',
        'dev': 'http://127.0.0.1:5000/auth'
    }

    data = {
        'client_id': client_id(),
        'client_secret': client_secret(),
        'code': session['temp_auth'].get('code', ''),
        'scope': session['temp_auth'].get('scope', ''),
        'context': session['temp_auth'].get('context', ''),
        'grant_type': 'authorization_code',
        'redirect_uri': redirect['dev'] if DEBUG else redirect['prod']
    }

    session.pop('temp_auth', None)

    response = requests.post(url, headers=headers, data=data).json()

    if 'error' in response:
        return render_template('error.html', message=response['error'])

    user_id = int(response['user'].get('id'))
    store_owner = StoreOwner.query.get(user_id)

    if store_owner is not None:
        db.session.delete(store_owner)

    db.session.add(StoreOwner(response))
    db.session.commit()

    return render_template('index.html')



@app.route("/icons/<file_name>.svg")
def get_icon(file_name):
    response = make_response(render_template(f'icons/{file_name}.svg'))
    response.mimetype = 'image/svg+xml'
    
    return response



@app.route("/scrape")
def init_scrape():
    settings = session['scrape']
    run_spider(settings)

    items = {'items': settings['items']}
    logger = settings['logger']

    return json.dumps(items if not 'error' in logger else logger)



@app.route('/import', methods=['POST'])
def verify_import():
    session['scrape'] = {
        'url': request.form['url'],
        'import_type': request.form['import-type'],
        'status': 'Connecting...',
        'items': [],
        'logger': {}, 
        'login': {
            'id': request.form['id'],
            'email': request.form['email'],
            'pass': request.form['password'],
        }
    }

    return render_template('import.html')



@app.route("/begin_import", methods=['POST'])
def begin_import():
    bc_data = session['bc_data']
    user_id = bc_data['user'].get('id')
    store_owner = StoreOwner.query.get(int(user_id))
    products = json.loads(request.form['products'])
    results = []

    if store_owner is not None:
        store = BigCommerceStore(store_owner, client_id(), client_secret())

    get_id = lambda r : r.json().get('data', {}).get('id', None) if r is not None else False
    get_opts = lambda r : r.json().get('data', {}).get('option_values', None) if r is not None else False
    get_json = lambda r : r.json() if r is not None and r.status_code != 200 else {}

    for product in products:
        product_resp = store.create_product(product)

        status = {
            'name': product['name'],
            'id': get_id(product_resp),
            'json': get_json(product_resp),
            'modifiers': []
        }

        if product_resp is not None and product_resp.status_code == 200:
            size_mod = store.create_size_modifier(status['id'], product)
            clr_mod = store.create_color_modifier(status['id'], product)
            mod_id = get_id(clr_mod['response'])

            status['modifiers'].extend((get_json(size_mod), get_json(clr_mod['response'])))

            for val, adj in zip(get_opts(clr_mod['response']), clr_mod['adjusters']):
                mod_update = store.update_modifier(status['id'], mod_id, val['id'], adj)

                status['modifiers'].append(get_json(mod_update))

        results.append(status)

    return render_template('results.html', data=json.dumps(results))



@app.route("/cancel_import", methods=['POST'])
def cancel_import():
    return render_template('import.html')



if __name__ == '__main__':
    app.run()
