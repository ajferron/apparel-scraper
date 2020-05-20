import requests
import json
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

client_id = ''
client_secret = ''

def parse_user(json):
    print('RESPONSE')
    print(json)
    print(json['access_token'])
    print(json['scope'])
    print(json['user'])
    print(json['context'])



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/auth')
def auth():
    temp_auth = {
        'code': request.args.get('code', ''),
        'scope': request.args.get('scope', ''),
        'context': request.args.get('context', '')
    }

    # Huge vulnerability, could be used to intercept auth token
    return render_template('auth.html', auth=json.dumps(temp_auth))


@app.route('/uninstall')
def uninstall():
    return render_template('uninstall.html')


@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        url = 'https://login.bigcommerce.com/oauth2/token'
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        temp_auth = json.loads(request.form['auth'])

        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': temp_auth['code'],
            'scope': temp_auth['scope'],
            'context': temp_auth['context'],
            'grant_type': 'authorization_code',
            'redirect_uri': 'http://127.0.0.1:5000/auth'
        }

        response = requests.post(url, headers=headers, data=data).json()

        if 'error' in response:
            return render_template('error.html', message='Unable to authorize, try again later.')
        else:
            parse_user(response)

    return render_template('index.html')


if __name__ == '__main__':
    app.debug = True
    app.run()
