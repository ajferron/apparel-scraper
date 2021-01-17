from flask import Flask, request, session, render_template, make_response, redirect
from utils import Logger, verify_sig, ScrapeJob
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import requests
import json
import os



# PROJECT STATE (January 9, 2021)

#   Add spiders for Trimark, Debco, TechnoSport
#   Upgrade to Bootstrap 5
#   Look into obfuscator
#   Create a table for jobs (not just scrapes), move meta
#   Fix alignment with varying status values in uploads.html
#   Clean up loggers, add logging to review.js, uploads.js



app = Flask(__name__)

# FLASK SESSION
app.config['SESSION_SECRET'] = os.getenv('SESSION_SECRET')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# BIGCOMMERCE OAUTH
app.config['APP_URL'] = os.getenv('APP_URL', 'http://127.0.0.1:3000')
app.config['APP_CLIENT_ID'] = os.getenv('APP_CLIENT_ID')
app.config['APP_CLIENT_SECRET'] = os.getenv('APP_CLIENT_SECRET')

# POSTRES CREDENTIALS
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SERVICES
app.config['SCRAPE_API'] = os.getenv('SCRAPE_API', 'http://apparel-scraper_scraper-api_1:5000')
app.config['BC_API'] = os.getenv('BC_API', 'http://apparel-scraper_bc-api_1:8000')

# DEBUGGING
app.config['DEBUG'] = os.getenv('DEBUG') != '0'
app.config['DEMO_ID'] = os.getenv('DEMO_ID', 0)
app.config['LOG'] = os.getenv('LOG') != '0'



app.secret_key = app.config['SESSION_SECRET']

logger = Logger('app', app.config['LOG'])

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
        self.owner_id = data.get('user', {}).get('id', '')
        self.access_token = data.get('access_token', '')
        self.store_hash = data.get('context', '').split('/')[1]
        self.username = data.get('user', {}).get('username', '')
        self.email = data.get('user', {}).get('email', '')
        self.scope = data.get('scope', '')



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



class ProductUpload(db.Model):
    __tablename__ = 'product_uploads'

    scrape_id = db.Column(db.String(), primary_key=True)
    owner_id = db.Column(db.Integer, unique=False)
    job_id = db.Column(db.String(), unique=False)
    meta = db.Column(db.String(), unique=False)
    status = db.Column(db.String(), unique=False)
    result = db.Column(db.String(), unique=False)

    def __init__(self, data):
        self.scrape_id = data.get('scrape_id', '')
        self.job_id = data.get('job_id', '')
        self.owner_id = data.get('owner_id', '')
        self.status = data.get('status', '')
        self.result = data.get('result', '')
        self.meta = data.get('meta', '')



@app.before_request
def reset_session_timeout():
    session.modified = True



@app.route('/<file_name>.svg', methods=['GET'])
def get_icon(file_name):
    response = make_response(render_template(f'icons/{file_name}.svg'))
    response.mimetype = 'image/svg+xml'

    return response



# BIG COMMERCE oAUTH

@app.route('/', methods=['GET'])
def index():
    if session.get('owner_id', 0):
        return render_template('index.html')

    else:
        payload = request.args.get('signed_payload', False)
        bc_data = verify_sig(payload, app.config['APP_CLIENT_SECRET'])

        if payload and bc_data:
            session['owner_id'] = int(bc_data['owner']['id'])

        if app.config['DEBUG']:
            session['owner_id'] = int(app.config['DEMO_ID'])

        if session.get('owner_id', 0):
            logger.success('Verified signature')

            return render_template('index.html')

    logger.error('Failed to verify signature')

    return render_template('error.html', msg='This web app can only be accessed through your Big Commerce store!')



@app.route('/uninstall')
def uninstall():
    payload = request.args.get('signed_payload', False)
    bc_data = verify_sig(payload, app.config['APP_CLIENT_SECRET'])

    if bc_data:
        owner_id = bc_data.get('owner', {}).get('id', 0)
        store_owner = StoreOwner.query.get(int(owner_id))

        if store_owner is not None:
            db.session.delete(store_owner)
            db.session.commit()

    return render_template('uninstall.html')



@app.route('/auth')
def auth():
    session['temp_auth'] = {
        'code': request.args.get('code', ''),
        'scope': request.args.get('scope', ''),
        'context': request.args.get('context', '')
    }

    return render_template('auth.html')



@app.route('/authorize', methods=['POST'])
def authorize():
    if not 'temp_auth' in session:
        return render_template('error.html', msg=f'Please authorize from Big Commerce', btn='OK', uri='/')

    response = requests.post(
        url='https://login.bigcommerce.com/oauth2/token', 
        headers={'content-type': 'application/x-www-form-urlencoded'},
        data={
            'client_id': app.config['APP_CLIENT_ID'],
            'client_secret': app.config['APP_CLIENT_SECRET'],
            'grant_type': 'authorization_code',
            'code': session['temp_auth'].get('code', ''),
            'scope': session['temp_auth'].get('scope', ''),
            'context': session['temp_auth'].get('context', ''),
            'redirect_uri': f'{app.config["APP_URL"]}/auth'
        }
    ).json()

    session.pop('temp_auth', None)

    if 'error' in response:
        logger.error(f"Failed to authorize app\nResponse {response['error']}")

        return render_template('error.html', msg=response['error'])

    owner_id = int(response.get('user', {}).get('id', 0))

    owner = StoreOwner.query.get(owner_id)
    config = ImportSettings.query.get(owner_id)

    if owner is not None:
        logger.info('Deleting outdated credentials from DB')

        db.session.delete(owner)
        db.session.delete(config)

    db.session.add(StoreOwner(response))
    db.session.add(ImportSettings(owner_id))
    db.session.commit()

    logger.success('Store owner committed to DB')

    return render_template('index.html')



 ######  ######## ######## ######## #### ##    ##  ######    ######
##    ## ##          ##       ##     ##  ###   ## ##    ##  ##    ##
##       ##          ##       ##     ##  ####  ## ##        ##
 ######  ######      ##       ##     ##  ## ## ## ##   ####  ######
      ## ##          ##       ##     ##  ##  #### ##    ##        ##
##    ## ##          ##       ##     ##  ##   ### ##    ##  ##    ##
 ######  ########    ##       ##    #### ##    ##  ######    ######

@app.route('/user-settings', methods=['GET'])
def user_settings():
    if not app.config['DEBUG']:
        return render_template('settings.html', settings={
            'sanmar': {"user_id": "12345", "email": "apparel@scraper.com", "password": "abcd12345", "markup": "15.00"},
            'debco': {"email": "", "password": "", "markup": "15.00"},
            'technosport': {"email": "apparel@scraper.com", "password": "abcd12345", "markup": "15.00"},
            'trimark': {"email": "apparel@scraper.com", "password": "abcd12345", "markup": "15.00"}
        })

    settings = ImportSettings.query.get(session['owner_id'])

    if settings:
        return render_template('settings.html', settings={
            'sanmar': json.loads(settings.sanmar_config),
            'debco': json.loads(settings.debco_config),
            'technosport': json.loads(settings.technosport_config),
            'trimark': json.loads(settings.trimark_config)
        })
    else:
        return render_template('settings.html')



@app.route('/user-settings', methods=['POST'])
def update_user_settings():
    if not app.config['DEBUG']:
        return render_template('settings.html', settings={
            'sanmar': {"user_id": "12345", "email": "apparel@scraper.com", "password": "abcd12345", "markup": "15.00"},
            'debco': {"email": "", "password": "", "markup": "15.00"},
            'technosport': {"email": "apparel@scraper.com", "password": "abcd12345", "markup": "15.00"},
            'trimark': {"email": "apparel@scraper.com", "password": "abcd12345", "markup": "15.00"}
        })

    else:
        supplier = request.form.get('supplier', '')
        settings = ImportSettings.query.get(session['owner_id'])

        if settings:
            config = {
                'email': request.form.get('email', ''),
                'password': request.form.get('password', ''),
                'markup': request.form.get('markup', '')
            }

            if supplier == 'sanmar':
                config['user_id'] = request.form.get('id', '')
                settings.sanmar_config = json.dumps(config)

            elif supplier == 'debco':
                settings.debco_config = json.dumps(config)

            elif supplier == 'technosport':
                settings.technosport_config = json.dumps(config)

            elif supplier == 'trimark':
                settings.trimark_config = json.dumps(config)

            db.session.commit()

        return render_template('settings.html', settings={
            'sanmar': json.loads(settings.sanmar_config),
            'debco': json.loads(settings.debco_config),
            'technosport': json.loads(settings.technosport_config),
            'trimark': json.loads(settings.trimark_config)
        })



##     ## ########  ##        #######     ###    ########   ######
##     ## ##     ## ##       ##     ##   ## ##   ##     ## ##    ##
##     ## ##     ## ##       ##     ##  ##   ##  ##     ## ##
##     ## ########  ##       ##     ## ##     ## ##     ##  ######
##     ## ##        ##       ##     ## ######### ##     ##       ##
##     ## ##        ##       ##     ## ##     ## ##     ## ##    ##
 #######  ##        ########  #######  ##     ## ########   ######

@app.route('/product-uploads', methods=['GET'])
def product_uploads():
    if 'owner_id' not in session:
        return render_template('error.html', msg='Session has no Owner ID!')

    uploads = ProductUpload.query.filter_by(owner_id=session['owner_id']).all()

    convert = lambda u : {
        'scrape_id': u.scrape_id,
        'job_id': u.job_id,
        'status': u.status,
        'result': json.loads(u.result),
        'meta': json.loads(u.meta)
    }

    uploads = list(map(convert, uploads))

    logger.info(f'Found {len(uploads)+1} uploads')

    return render_template('uploads.html', data=json.dumps(uploads))



@app.route('/product-uploads', methods=['DELETE'])
def del_product_uploads():
    scrape_id = request.get_json().get('scrape_id', None)

    if scrape_id:
        row = ProductUpload.query.get(scrape_id)

        if row is not None:
            db.session.delete(row)
            db.session.commit()

            return json.dumps({'data': None, 'error': None})

        return json.dumps({'data': None, 'error': 'scrape_id doesn\'t exist'})

    return json.dumps({'data': None, 'error': 'No scrape_id given'})



@app.route('/product-review', methods=['GET'])
def product_review():
    job_id = request.args.get('job_id', None)
    
    if 'owner_id' not in session or not job_id:
        return render_template('error.html', msg='Could not retrieve job data!')

    uploads = ProductUpload.query.filter_by(job_id=job_id).all()

    convert = lambda u : json.loads(u.result)

    uploads = list(map(convert, uploads))

    logger.info(f'Found {len(uploads)} uploads')
    logger.info(json.dumps(uploads, indent=2))

    return render_template('review.html', data=json.dumps(uploads))



@app.route('/upload-status', methods=['GET'])
def upload_status():
    scrape_ids = json.loads(request.args.get('scrape_ids', '[]'))

    results = ProductUpload.query.filter(
        ProductUpload.scrape_id.in_(scrape_ids)
    ).all()

    convert = lambda u : (u.scrape_id, u.status)

    results = dict(map(convert, results))

    return json.dumps(results)



 ######   ######  ########             ###    ########  ####
##    ## ##    ## ##     ##           ## ##   ##     ##  ##
##       ##       ##     ##          ##   ##  ##     ##  ##
 ######  ##       ########  ####### ##     ## ########   ##
      ## ##       ##   ##           ######### ##         ##
##    ## ##    ## ##    ##          ##     ## ##         ##
 ######   ######  ##     ##         ##     ## ##        ####

@app.route('/init-import', methods=['POST'])
def init_import():
    if 'owner_id' not in session:
        return render_template('error.html', msg='Session has no Owner ID!')

    try:
        logger.info('Starting new scrape job')

        scrape_job = ScrapeJob({
            'url': request.form['url'],
            'api': app.config['SCRAPE_API'],
            'job_type': request.form['import-type'],
            'supplier': request.form['supplier'],
            'settings': ImportSettings.query.get(session['owner_id']),
            'logger': Logger('scrape_job', app.config['LOG'])
        })

        scrape_job.run()

        logger.success('Scraper run complete')
        logger.success(scrape_job.urls)

        for url in scrape_job.urls:
            logger.info('Pushing upload to DB')
            logger.info(url)

            db.session.add(ProductUpload({
                'scrape_id': url.get('id'),
                'owner_id': session['owner_id'],
                'job_id': scrape_job.job_id,
                'meta': scrape_job.json(),
                'status': 'scraping',
                'result': '{}'
            }))

        db.session.commit()

    except TypeError as e:
        return render_template('error.html', msg=e.args[0])

    except KeyError as e:
        return render_template('error.html', msg=e.args[0], btn='Add', uri='/user-settings')

    return redirect('/product-uploads')



# BIG COMMERCE API

@app.route("/categories", methods=['GET'])
def get_categories():
    logger.info('Getting product categories from store')

    # requests.get() categories from Big Commerce API

    if app.config['DEBUG']:
        with open('demo/demo-categories.json') as categories:
            return json.loads(categories.read())

    return '{data: []}'



@app.route("/create-products", methods=['POST'])
def create_products():
    owner_id = session['owner_id']

    products = json.loads(request.form['products'])

    return render_template('uploads.html')



if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))

    app.run(host='0.0.0.0', port=port)
