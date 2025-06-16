from flask import Blueprint
from splash.blueprints.api.v1.sharex import sharex_bp
from splash.blueprints.api.v1.images import images_bp

v1_bp = Blueprint('v1', __name__, url_prefix='/v1')
v1_bp.register_blueprint(images_bp)
v1_bp.register_blueprint(sharex_bp)
