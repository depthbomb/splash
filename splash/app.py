from flask import Flask
from loguru import logger
from splash.logger import configure_logging
from splash.blueprints import register_blueprints
from splash.lifecycle import register_lifecycle_hooks
from splash.error_handlers import register_error_handlers
from splash.providers.ORJSONProvider import ORJSONProvider
from splash.lib.features import get_all_features, create_feature_flag

def create_app():
    create_feature_flag('DAILY_RATE_LIMIT_ENABLED', True)
    create_feature_flag('PRETTIFY_RENDERED_JSON_ENABLED', True)
    create_feature_flag('MAINTENANCE_MODE_ENABLED', False)

    app = Flask(__name__)
    app.json = ORJSONProvider(app)
    app.url_map.strict_slashes = False

    configure_logging(app)
    register_lifecycle_hooks(app)
    register_blueprints(app)
    register_error_handlers(app)

    logger.info(f'App created with features {get_all_features()}')

    return app
