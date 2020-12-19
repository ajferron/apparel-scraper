from flask import Flask, request, session, render_template, make_response
from utils import BigCommerceStore, Logger, verify_sig, run_spider, get_result
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import dotenv
import requests
import json
import os



# PROJECT STATE (July 31, 2020)

#   Add spiders for Trimark, Debco, TechnoSport
#   Figure out how to communicate with spiders
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
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


def client_id():
    return app.config['APP_CLIENT_ID']


def client_secret():
    return app.config['APP_CLIENT_SECRET']


def session_secret():
    return app.config['SESSION_SECRET']


def redirect_uri():
    return 'http://127.0.0.1:3000/auth' if app.debug else 'https://apparel-scraper.herokuapp.com/auth'



app.secret_key = session_secret()

app.debug = os.getenv('DEBUG')

logger = Logger(app.debug)
db = SQLAlchemy(app)

logger.success('App Initialized')



class StoreOwner(db.Model):
    __tablename__ = 'users'

    owner_id = db.Column(db.Integer, primary_key=True)
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
        self.owner_id = data['user'].get('id')
        self.scope = data['scope']



@app.before_request
def reset_session_timeout():
    session.modified = True



@app.route('/')
def index():
    payload = request.args.get('signed_payload', False)

    if not session.get('bc_data', False):
        session['bc_data'] = verify_sig(payload, client_secret())

        if payload and session['bc_data']:
            logger.success('Verified signature')
        else:
            logger.error('Failed to verify signature')

            if (not app.debug):
                return render_template('error.html', msg='This web app can only be accessed through your Big Commerce store!')

        logger.info('Updated bc_data')

        session.permanent = True

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
    response = requests.post(
        url='https://login.bigcommerce.com/oauth2/token', 
        headers={'content-type': 'application/x-www-form-urlencoded'},
        data={
            'client_id': client_id(),
            'client_secret': client_secret(),
            'grant_type': 'authorization_code',
            'code': session['temp_auth'].get('code', ''),
            'scope': session['temp_auth'].get('scope', ''),
            'context': session['temp_auth'].get('context', ''),
            'redirect_uri': redirect_uri()
        }
    ).json()

    session.pop('temp_auth', None)

    if 'error' in response:
        logger.error(f"Failed to authorize app\nResponse {response['error']}")

        return render_template('error.html', msg=response['error'])

    user_id = int(response['user'].get('id'))
    owner = StoreOwner.query.get(user_id)

    if owner is not None:
        logger.info('Deleting outdated credentials from DB')
        db.session.delete(owner)

    db.session.add(StoreOwner(response))
    db.session.commit()

    logger.success('Store owner committed to DB')

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



@app.route('/import-review', methods=['POST'])
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
    owner = StoreOwner.query.get(int(user_id))
    products = json.loads(request.form['products'])

    if owner is not None:
        store = BigCommerceStore(owner, client_id(), client_secret())
        logger.success('Set up user store')
    else:
        logger.error('Import Failed: could not find store owner')
        return render_template('results.html', message='Could not find your store!')

    if 'uploads' not in session:
        session['uploads'] = []

    for product in products:
        time = datetime.now().strftime('%b. %d, %Y at %I:%M %p')
        deferred = store.create_product(product)

        session['uploads'].append({
            'created': time,
            'active': True,
            'thread': deferred.stash()
        })

    return render_template('results.html', data=json.dumps([]))



@app.route("/product-uploads", methods=['GET'])
def product_uploads():
    for upload in session['uploads']:
        if upload['active']:
            result = get_result(upload)

            if result:
                upload['active'] = False
                upload['result'] = result

    return json.dumps(session['uploads'])



@app.route("/active-uploads", methods=['GET'])
def active_uploads():
    active = []

    for upload in session['uploads']:
        if upload['active']:
            result = get_result(upload)

            if result:
                upload['active'] = False
                upload['result'] = result
            else:
                active.append(upload)

    return json.dumps({'active': len(active)})



if __name__ == '__main__':
    app.run(port=3000)
