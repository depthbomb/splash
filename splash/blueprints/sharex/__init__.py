from typing import cast
from orjson import dumps
from base64 import b64encode
from splash.db.models import User
from splash.decorators.common import no_cache_control
from splash.decorators.auth import requires_authentication
from flask import g, url_for, request, Response, Blueprint

sharex_bp = Blueprint('sharex', __name__, url_prefix='/sharex')

@sharex_bp.get('/')  # GET /sharex
@no_cache_control
@requires_authentication(redirect_to_auth=True)
def get_config():
    use_raw = request.args.get('raw', 'false').lower() == 'true'
    user = cast(User, g.user)
    sub = user.sub
    api_key = user.api_key
    credentials = f'{sub}:{api_key}'.encode()

    sharex_config = {
        'Version': '17.0.0',
        'Name': 'Splash',
        'DestinationType': 'ImageUploader',
        'RequestMethod': 'PUT',
        'RequestURL': url_for('images.upload_image', _external=True),
        'Parameters': {
            'sharex': 'true'
        },
        'Headers': {
            'Authorization': f'Basic {b64encode(credentials).decode()}',
        },
        'Body': 'MultipartFormData',
        'FileFormName': 'file',
        'URL': '{json:result.url}',
        'ThumbnailURL': '{json:result.url}',
        'DeletionURL': '{json:result.deletion_url}',
        'ErrorMessage': '{json:result.message}',
    }

    if use_raw:
        return sharex_config

    return Response(
            dumps(sharex_config),
            mimetype='application/json',
            headers={
                'Content-Disposition': 'attachment; filename=Splash.sxcu'
            }
    )
