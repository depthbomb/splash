from typing import cast
from orjson import dumps
from base64 import b64encode
from splash.db.models import User
from flask import g, url_for, redirect, Blueprint
from splash.http.response import plaintext_response
from splash.decorators.common import add_cache_control
from splash.decorators.auth import requires_authentication

index_bp = Blueprint('index', __name__)

@index_bp.get('/')
@requires_authentication(redirect_to_auth=True)
def index():
    user = cast(User, g.user)
    credentials = f'{user.sub}:{user.api_key}'.encode()
    header_value = b64encode(credentials).decode()

    return plaintext_response('\n'.join([
        "   .---. ,---.  ,-.      .--.     .---. .-. .-. ",
        "  ( .-._)| .-.\ | |     / /\ \   ( .-._)| | | | ",
        " (_) \   | |-' )| |    / /__\ \ (_) \   | `-' | ",
        " _  \ \  | |--' | |    |  __  | _  \ \  | .-. | ",
        "( `-'  ) | |    | `--. | |  |)|( `-'  ) | | |)| ",
        " `----'  /(     |( __.'|_|  (_) `----'  /(  (_) ",
        "        (__)    (_)                    (__)     ",
        "\n---\n",
        "\n## User Info\n",
        f"Username: {user.username}",
        f"Sub: {user.sub}",
        f"API Key: {user.api_key}",
        "\n## Authentication\n",
        "Some endpoints require authentication.",
        "Requests can be authenticated either by including your API key in the request as a `?api_key=` query parameter or by using basic authorization `base64('sub:api_key')`:",
        "\n```",
        f"?api_key={user.api_key}",
        f"Authorization: Basic {header_value}",
        "```",
        "\n## Endpoints\n",
        "GET /image/{uid}",
        "\tReturn basic info about an image record.",
        "GET /image/{uid}.{extension}",
        "\tReturns an image response.",
        "PUT /image",
        "\tCreates an image record with a randomly-assigned UID.",
        "\tThe successful response will include a `deletion_key` which should be kept secret as it is used to delete the image later.",
        "DELETE /image/{uid}/{deletion_key}",
        "\tDeletes an image record and the corresponding file.",
        "\n## Requests\n",
        "All requests must have a non-empty user agent header.",
        "Respect rate limits. Most endpoints return headers (`X-RateLimit-...`) that you should use to avoid being rate limited.",
        "\n## Responses\n",
        "All responses inherit a common shape:",
        "```json",
        f"{dumps({
                'request_id': "str",
                'status_code': "integer",
                'result': "unknown"
        }).decode()}",
        "```",
        "...with `result` being a different shape depending on the endpoint and response status.",
        "Error responses will always at least include a `message` property inside `result` describing the error.",
        "\n## ShareX Support\n",
        f"Splash supports uploading images via ShareX. You can download the custom uploader config here: {url_for('api.v1.sharex.get_config', _external=True)}",
        "This config is exclusive to **YOU** because it contains your credentials. Do not share it with anyone."
    ]))

@index_bp.get('/i/<string:uid>')
def get_image_short(uid: str):
    return redirect(url_for('api.v1.images.get_image', uid=uid))

@index_bp.get('/robots.txt')
@add_cache_control(max_age=60 * 60 * 60 * 24)
def robots_txt():
    return plaintext_response('\n'.join([
        'User-agent: *',
        'Disallow: /',
        'Disallow: /api',
        'Disallow: /auth',
        'Disallow: /health'
    ]))
