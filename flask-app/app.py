from flask import Flask, request, session, render_template, make_response
from utils import Logger, verify_sig
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
#   Look into obfuscator


# OTHER IMPROVEMENTS

#   Have users create an account with the app
#   Allow them to save login information for suppliers



app = Flask(__name__)


if os.path.exists('.env'):
    dotenv.load_dotenv()

app.config['APP_CLIENT_ID'] = os.getenv('APP_CLIENT_ID')
app.config['APP_CLIENT_SECRET'] = os.getenv('APP_CLIENT_SECRET')
app.config['SESSION_SECRET'] = os.getenv('SESSION_SECRET')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['DEBUG'] = lambda : os.getenv('DEBUG') != '0'
app.config['DEMO'] = lambda : os.getenv('DEMO') != '0'
app.config['LOG'] = lambda : os.getenv('LOG') != '0'



def client_id():
    return app.config['APP_CLIENT_ID']


def client_secret():
    return app.config['APP_CLIENT_SECRET']


def redirect_uri():
    return 'http://127.0.0.1:3000/auth' if app.config['DEBUG']() else 'https://apparel-scraper-app.herokuapp.com/auth'



app.secret_key = app.config['SESSION_SECRET']

logger = Logger(app.config['LOG']())

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
        self.owner_id = data['user'].get('id')
        self.access_token = data['access_token']
        self.store_hash = data['context'].split('/')[1]
        self.username = data['user'].get('username')
        self.email = data['user'].get('email')
        self.scope = data['scope']



class ImportSettings(db.Model):
    __tablename__ = 'import_settings'

    owner_id = db.Column(db.Integer, primary_key=True)
    sanmar_config = db.Column(db.String(), unique=False)
    debco_config = db.Column(db.String(), unique=False)
    technosport_config = db.Column(db.String(), unique=False)
    trimark_config = db.Column(db.String(), unique=False)

    def __init__(self, owner_id, **kwargs):
        self.owner_id = owner_id
        self.sanmar_config = kwargs.get('sanmar', '{}')
        self.debco_config = kwargs.get('debco', '{}')
        self.technosport_config = kwargs.get('technosport', '{}')
        self.trimark_config = kwargs.get('trimark', '{}')



@app.before_request
def reset_session_timeout():
    session.modified = True



@app.route('/', methods=['GET'])
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

    if 'uploads' not in session:
        session['uploads'] = []

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
    if not 'temp_auth' in session:
        return render_template('error.html', msg=f'Please authorize from Big Commerce', btn='OK', uri='/')

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
    config = ImportSettings.query.get(user_id)

    if owner is not None:
        logger.info('Deleting outdated credentials from DB')
        db.session.delete(owner)
        db.session.delete(config)

    db.session.add(StoreOwner(response))
    db.session.add(ImportSettings(user_id))
    db.session.commit()

    logger.success('Store owner committed to DB')

    return render_template('index.html')



@app.route('/icons/<file_name>.svg', methods=['GET'])
def get_icon(file_name):
    response = make_response(render_template(f'icons/{file_name}.svg'))
    response.mimetype = 'image/svg+xml'

    return response



@app.route("/categories", methods=['GET'])
def get_categories():
    logger.info('Getting product categories from store')

    # requests.get() categories from Big Commerce API

    if app.config['DEMO']():
        with open('demo/demo-categories.json') as categories:
            return json.loads(categories.read())

    return '{data: []}'



@app.route('/import-review', methods=['POST'])
def import_review():
    if app.config['DEMO']():
        login_details = '{}'

    else:
        owner_id = session['bc_data'].get('owner').get('id')
        settings = ImportSettings.query.get(owner_id)
        supplier = request.form['supplier']

        if supplier == 'sanmar':
            login_details = settings.sanmar_config

        elif supplier == 'debco':
            login_details = settings.debco_config

        elif supplier == 'technosport':
            login_details = settings.technosport_config

        elif supplier == 'trimark':
            login_details = settings.trimark_config

        else:
            return render_template('error.html', msg='Could not import from the given URL')

        if login_details == '{}':
            return render_template('error.html', msg=f'Please add login credentials for {supplier}', btn='Add', uri='/user-settings')

    session['scrape'] = {
        'url': request.form['url'],
        'supplier': request.form['supplier'],
        'import_type': request.form['import-type'],
        'login': json.loads(login_details),
        'items': []
    }

    return render_template('import.html')



@app.route('/scrape', methods=['GET'])
def init_scrape():
    logger.info('Scraping product data')

    if app.config['DEMO']():
        with open('demo/demo-product.json') as product:
            return product.read()

    # requests.post() to Scrapy cluster REST API /feed endpoint
    # run_spider(session['scrape'])

    return {'items': session['scrape'].get('items')}



@app.route("/import", methods=['POST'])
def import_products():
    if app.config['DEMO']():
        pass

    else:
        bc_data = session['bc_data']
        user_id = bc_data['user'].get('id')

        products = json.loads(request.form['products'])

        # owner = StoreOwner.query.get(int(user_id))

        # if owner is not None:
        #     store = BigCommerceStore(owner, client_id(), client_secret())
        #     logger.success('Set up user store')
        # else:
        #     return render_template('results.html', message='Could not find your store!')

        # batch = [] # Change this to dict

        # for product in products:
        #     time = datetime.now().strftime('%b. %d, %Y at %I:%M %p')
        #     deferred = store.create_product(product)

        #     batch.append({
        #         'created': time,
        #         'product': product,
        #         'thread': deferred.stash(),
        #         'active': True
        #     })

        # session['uploads'].append(batch)

    return render_template('results.html', data=json.dumps([]))



@app.route('/user-settings', methods=['GET'])
def user_settings():
    if app.config['DEMO']():
        return render_template('settings.html',
            sanmar={"user_id": "12345", "email": "apparel@scraper.com", "password": "abcd12345", "markup": "15.00"},
            debco={"email": "", "password": "", "markup": "15.00"},
            technosport={"email": "apparel@scraper.com", "password": "abcd12345", "markup": "15.00"},
            trimark={"email": "apparel@scraper.com", "password": "abcd12345", "markup": "15.00"}
        )

    owner_id = session['bc_data'].get('owner').get('id')
    settings = ImportSettings.query.get(owner_id)

    return render_template('settings.html',
        sanmar=json.loads(settings.sanmar_config),
        debco=json.loads(settings.debco_config),
        technosport=json.loads(settings.technosport_config),
        trimark=json.loads(settings.trimark_config)
    )



@app.route('/user-settings', methods=['POST'])
def update_user_settings():
    if app.config['DEMO']():
        return render_template('settings.html',
            sanmar={"user_id": "12345", "email": "apparel@scraper.com", "password": "abcd12345", "markup": "15.00"},
            debco={"email": "", "password": "", "markup": "15.00"},
            technosport={"email": "apparel@scraper.com", "password": "abcd12345", "markup": "15.00"},
            trimark={"email": "apparel@scraper.com", "password": "abcd12345", "markup": "15.00"}
        )

    else:
        supplier = request.form.get('supplier', '')
        owner_id = session['bc_data'].get('owner').get('id')
        settings = ImportSettings.query.get(owner_id)

        if settings:
            config = {
                'user_id': request.form.get('id', ''),
                'email': request.form.get('email', ''),
                'password': request.form.get('password', ''),
                'markup': request.form.get('markup', '')
            }

            if supplier == 'sanmar':
                settings.sanmar_config = json.dumps(config)

            elif supplier == 'debco':
                settings.debco_config = json.dumps(config)

            elif supplier == 'technosport':
                settings.technosport_config = json.dumps(config)

            elif supplier == 'trimark':
                settings.trimark_config = json.dumps(config)

            db.session.commit()

        return render_template('settings.html',
            sanmar=json.loads(settings.sanmar_config),
            debco=json.loads(settings.debco_config),
            technosport=json.loads(settings.technosport_config),
            trimark=json.loads(settings.trimark_config)
        )



@app.route('/product-uploads', methods=['GET'])
def product_uploads():
    # if session['uploads'] == []:
        # query db for all uploads 
        # store uploads in session
    
    # return array of {upload_id: xxx, status: ---}

    return json.dumps(session['uploads'])



@app.route('/upload-status', methods=['GET'])
def active_uploads():
    # req contains list of upload_ids
    # session['bc_data'] contains owner_id
    # query db for all the upload_ids with the owner_id
    # respond with array of {upload_id: xxx, status: ---}

    return '{}'
 


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    app.run(host='0.0.0.0', port=port)
