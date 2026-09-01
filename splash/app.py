from flask import Flask
from loguru import logger
from splash.env import APP_SECRET
from splash import MAX_UPLOAD_SIZE
from splash.logger import configure_logging
from splash.blueprints import register_blueprints
from werkzeug.middleware.proxy_fix import ProxyFix
from splash.lifecycle import register_lifecycle_hooks
from splash.error_handlers import register_error_handlers
from splash.providers.ORJSONProvider import ORJSONProvider
from splash.lib.features import get_all_features, create_feature_flag
from splash.env import TRUSTED_HOSTS, TRUSTED_PROXY_COUNT, OIDC_TIMEOUT_SECONDS

def _validate_runtime_config() -> None:
    if APP_SECRET.strip() == '':
        raise RuntimeError('APP_SECRET must be configured and non-empty')
    if TRUSTED_PROXY_COUNT < 0:
        raise RuntimeError('TRUSTED_PROXY_COUNT must be non-negative')
    if OIDC_TIMEOUT_SECONDS <= 0:
        raise RuntimeError('OIDC_TIMEOUT_SECONDS must be positive')

def _ensure_feature_flag(name: str, enabled: bool) -> None:
    if not any(feature.name == name for feature in get_all_features()):
        create_feature_flag(name, enabled)

def create_app():
    _validate_runtime_config()

    _ensure_feature_flag('DAILY_RATE_LIMIT_ENABLED', True)
    _ensure_feature_flag('PRETTIFY_RENDERED_JSON_ENABLED', True)
    _ensure_feature_flag('MAINTENANCE_MODE_ENABLED', False)

    app = Flask(__name__, static_folder='../static', static_url_path='')
    app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE + (1024 * 1024)
    app.config['TRUSTED_HOSTS'] = TRUSTED_HOSTS or None
    if TRUSTED_PROXY_COUNT:
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=TRUSTED_PROXY_COUNT,
            x_proto=TRUSTED_PROXY_COUNT,
        )
    app.json = ORJSONProvider(app)
    app.url_map.strict_slashes = False

    configure_logging(app)
    register_lifecycle_hooks(app)
    register_blueprints(app)
    register_error_handlers(app)

    logger.info(f'App created with features {get_all_features()}')

    return app
