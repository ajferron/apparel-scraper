from flask import Flask , render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from scrapy.crawler import CrawlerRunner
from scrapy.signalmanager import dispatcher
from scrapy import signals
from scraper import ProductSpider
import crochet
import requests
import json
import time


app = Flask(__name__)

runner = CrawlerRunner()

crochet.setup()

output = []

def parse_user(json):
    print('RESPONSE')
    print(json)
    print(json['access_token'])
    print(json['scope'])
    print(json['user'].get('id'))
    print(json['user'].get('username'))
    print(json['user'].get('email'))
    print(json['context'])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    url = request.form['url']

    if len(url):
        return redirect(url_for('scrape', url=url))

    return render_template('index.html')


@app.route('/auth')
def auth():
    temp_auth = {
        'code': request.args.get('code', ''),
        'scope': request.args.get('scope', ''),
        'context': request.args.get('context', '')
    }

    # Huge vulnerability, could be used to intercept auth token
    # Generate random keys to add encryption keys as values to a dict
    # Send the dict key to the template, extract it to access the decryption key
    return render_template('auth.html', auth=json.dumps(temp_auth))


@app.route('/authorize', methods=['POST'])
def authorize():
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


@app.route('/uninstall')
def uninstall():
    return render_template('uninstall.html')


@app.route("/scrape")
def scrape():
    scrape_with_crochet(url=request.args['url']) # Passing that URL to our Scraping Function
    
    return render_template('index.html') # Returns the scraped data after being running for 20 seconds.


@crochet.wait_for(timeout=60)
def scrape_with_crochet(url):
    dispatcher.connect(_crawler_result, signal=signals.item_scraped)
    eventual = runner.crawl(ProductSpider, start_urls=[url])

    return eventual


def _crawler_result(item, response, spider):
    output.append(dict(item))
    print(item)
    


if __name__ == '__main__':
    app.debug = True
    app.run()
