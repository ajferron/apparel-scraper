from flask import Blueprint, request
from flask import current_app as app
from flask_sqlalchemy import SQLAlchemy
from .model.store import BigCommerceStore


api_bp = Blueprint(
    'api_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


@api_bp.route('/', methods=['GET'])
def index():
    print(request.args.get('owner_id', 0), flush=True)
    print(app.config['APP_CLIENT_ID'], flush=True)
    print(app.config['APP_CLIENT_SECRET'], flush=True)

    return request.get_json()


@api_bp.route('/feed', methods=['POST'])
def feed():
    product = request.get_json()

    # Put this in a try/catch
    store = BigCommerceStore({
        'store_hash': request.args.get('store_hash', 0),
        'access_token': request.args.get('access_token', 0),
        'client_secret': app.config['APP_CLIENT_ID'],
        'client_id': app.config['APP_CLIENT_SECRET']
    })

    return store.create_product(product)
