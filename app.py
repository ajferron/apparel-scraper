from flask import Flask, request, session, render_template, make_response, jsonify, url_for
from utils import verify_payload, parse_user, test_data, run_spider
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
     
    def __init__(self, json):
        self.store_hash = json['access_token']
        self.access_token = json['context'].split('/')[1]
        self.username = json['user'].get('username')
        self.email = json['user'].get('email')
        self.id = json['user'].get('id')
        self.scope = json['scope']



@app.route('/')
def index():
    payload = request.args.get('signed_payload', '')
    data = verify_payload(payload, client_secret()) if payload else {}
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



@app.route('/import', methods=['POST'])
def verify_import():
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

    return render_template('import.html')



@app.route('/authorize', methods=['POST'])
def authorize():
    url = 'https://login.bigcommerce.com/oauth2/token'
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    redirect = {
        'prod': 'https://supplier-scraper.herokuapp.com/auth',
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
        return render_template('error.html', message=response.error)

    return render_template('index.html')



@app.route("/icons/<file_name>.svg")
def get_icon(file_name):
    response = make_response(render_template(f'icons/{file_name}.svg'))
    response.mimetype = 'image/svg+xml'
    
    return response



@app.route("/scrape")
def init_scrape():
    if DEBUG: return test_data

    settings = session['scrape']
    run_spider(settings)

    return json.dumps(settings['items'])



if __name__ == '__main__':
    app.debug = True
    app.run()
