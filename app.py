from flask import Flask, request, session, render_template, make_response
from utils import Logger, BigCommerceStore, verify_sig, run_spider
from flask_sqlalchemy import SQLAlchemy
import dotenv
import requests
import json
import os



# PROJECT STATE (July 18, 2020)

#   Imports are too slow (use corchet with EventualResult)
#   Add spiders for Trimark, Debco, TechnoSport
#   Figure out how to communicate with spiders
#   Remove hardcoded site data
#   Make sure you can't access cookies from client
#   Set up error screen
#   Look into obfuscator


# OTHER IMPROVEMENTS

#   Have users create an account with the app
#   Allow them to save login information for suppliers



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


app.debug = os.getenv('DEBUG')
app.secret_key = session_secret()
logger = Logger(app.debug)
db = SQLAlchemy(app)

logger.success('app initialized')


class StoreOwner(db.Model):
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

    if not session.get('bc_data', False):
        session['bc_data'] = verify_sig(payload, client_secret())

        if payload and session['bc_data']:
            logger.success('Verified signature')
        else:
            logger.error('Failed to verify signature')

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
        'grant_type': 'authorization_code',
        'code': session['temp_auth'].get('code', ''),
        'scope': session['temp_auth'].get('scope', ''),
        'context': session['temp_auth'].get('context', ''),
        'redirect_uri': redirect['dev'] if app.debug else redirect['prod']
    }

    session.pop('temp_auth', None)

    response = requests.post(url, headers=headers, data=data).json()

    if 'error' in response:
        logger.error(f"Failed to authorize app\nResponse {response['error']}")

        return render_template('error.html', message=response['error'])

    user_id = int(response['user'].get('id'))
    store_owner = StoreOwner.query.get(user_id)

    if store_owner is not None:
        logger.info('Deleting outdated credentials from DB')
        db.session.delete(store_owner)

    db.session.add(StoreOwner(response))
    db.session.commit()

    logger.info('Store owner committed to DB')

    return render_template('index.html')



@app.route("/icons/<file_name>.svg")
def get_icon(file_name):
    response = make_response(render_template(f'icons/{file_name}.svg'))
    response.mimetype = 'image/svg+xml'

    return response



@app.route("/scrape")
def init_scrape():
    logger.info('Scraping product data')

    if app.debug:
        with open('demo-product.json') as product:
            return product.read()

    run_spider(session['scrape'])

    return {'items': session['scrape'].get('items')}



@app.route("/categories", methods=['GET'])
def get_categories():
    logger.info('Getting product categories from store')

    if app.debug:
        with open('demo-categories.json') as categories:
            return json.loads(categories.read())

    bc_data = session['bc_data']
    user_id = bc_data['user'].get('id')
    store_owner = StoreOwner.query.get(int(user_id))

    store = BigCommerceStore(store_owner, client_id(), client_secret())

    data = store.get_categories()

    return data.json()



@app.route('/import_review', methods=['POST'])
def import_review():
    session['scrape'] = {
        'url': request.form['url'],
        'supplier': request.form['supplier'],
        'import_type': request.form['import-type'],
        'items': [],
        'login': {
            # 'id': request.form['id'],
            # 'email': request.form['email'],
            # 'pass': request.form['password'],
        }
    }

    return render_template('import.html')



@app.route("/import", methods=['POST'])
def import_products():
    bc_data = session['bc_data']
    user_id = bc_data['user'].get('id')
    store_owner = StoreOwner.query.get(int(user_id))
    products = json.loads(request.form['products'])
    results = []

    if store_owner is not None:
        store = BigCommerceStore(store_owner, client_id(), client_secret())

    get_id = lambda r : r.json().get('data', {}).get('id', None) if r is not None else False
    get_url = lambda r : r.json().get('data', {}).get('custom_url', {}).get('url', None) if r is not None else False
    get_opts = lambda r : r.json().get('data', {}).get('option_values', None) if r is not None else False
    get_json = lambda r : r.json() if r is not None and r.status_code != 200 else None

    for product in products:
        product_resp = store.create_product(product)

        status = {
            'name': product['name'],
            'id': get_id(product_resp),
            'url': get_url(product_resp),
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



if __name__ == '__main__':
    app.run()
