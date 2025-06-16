from flask import request
from flask import Response, Blueprint
from splash.http.response import abort_if, json_response
from splash.lib.features import get_feature, get_all_features, get_enabled_features, get_disabled_features

features_bp = Blueprint('features', __name__, url_prefix='/_features')

@features_bp.before_request
def verify_app_secret() -> None:
    incoming_secret = request.args.get('secret', None)

    abort_if(incoming_secret is None, 401, message='Missing app secret key')

@features_bp.get('')
def list_features() -> Response:
    features = [{
        'name': feature.name,
        'enabled': feature.enabled,
        'description': feature.description
    } for feature in get_all_features()]

    return json_response(features)

@features_bp.get('/enabled')
def list_enabled_features() -> Response:
    features = [{
        'name': feature.name,
        'enabled': feature.enabled,
        'description': feature.description
    } for feature in get_enabled_features()]

    return json_response(features)

@features_bp.get('/disabled')
def list_disabled_features() -> Response:
    features = [{
        'name': feature.name,
        'enabled': feature.enabled,
        'description': feature.description
    } for feature in get_disabled_features()]

    return json_response(features)

@features_bp.put('/toggle/<flag_name>')
def toggle_feature(flag_name: str) -> Response:
    feature = get_feature(flag_name)

    abort_if(feature is None, 404, message=f'Feature flag {flag_name} does not exist')

    feature_enabled = feature.enabled
    feature.toggle()

    return json_response({
        'previous': feature_enabled,
        'current': feature.enabled
    })

@features_bp.put('/enable/<flag_name>')
def enable_feature(flag_name: str) -> Response:
    feature = get_feature(flag_name)

    abort_if(feature is None, 404, message=f'Feature flag {flag_name} does not exist')

    feature_enabled = feature.enabled
    feature.enable()

    return json_response({
        'previous': feature_enabled,
        'current': feature.enabled
    })

@features_bp.put('/disable/<flag_name>')
def disable_feature(flag_name: str) -> Response:
    feature = get_feature(flag_name)

    abort_if(feature is None, 404, message=f'Feature flag {flag_name} does not exist')

    feature_enabled = feature.enabled
    feature.disable()

    return json_response({
        'previous': feature_enabled,
        'current': feature.enabled
    })
