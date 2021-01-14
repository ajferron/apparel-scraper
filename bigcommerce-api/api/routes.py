from flask import Blueprint, render_template
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
    return 'hello world'


@api_bp.route('/feed', methods=['POST'])
def feed():
    pass
