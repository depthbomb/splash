from typing import cast
from itsdangerous import BadData
from splash.db.models import User
from authlib.oauth2 import OAuth2Error
from requests import RequestException
from datetime import datetime, timedelta, timezone
from splash.http.response import json_error
from splash.lib.id_generator import IDGenerator
from authlib.common.security import generate_token
from sqlalchemy.orm.session import Session as SASession
from splash.lib.rate_limits import get_or_create_bucket
from authlib.integrations.requests_client import OAuth2Session
from splash.serializers import previous_url_serializer, user_session_serializer
from flask import g, abort, url_for, request, redirect, Response, Blueprint, after_this_request
from urllib.parse import urlsplit
from splash.env import OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, OIDC_TOKEN_ENDPOINT, OIDC_USERINFO_ENDPOINT, OIDC_AUTHORIZE_ENDPOINT, OIDC_TIMEOUT_SECONDS

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
auth_bucket = get_or_create_bucket('auth', '1/second')

def _secure_cookie() -> bool:
    return request.is_secure

def _is_local_redirect(target: str) -> bool:
    parsed = urlsplit(target)
    return parsed.scheme == '' and parsed.netloc == '' and target.startswith('/')

@auth_bp.get('/start')
def start_flow():
    client = OAuth2Session(OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, code_challenge_method='S256', scope='openid email profile groups')
    code_verifier = generate_token(48)
    uri, state = client.create_authorization_url(
            OIDC_AUTHORIZE_ENDPOINT,
            redirect_uri=url_for('auth.callback', _external=True),
            code_verifier=code_verifier,
    )

    res = redirect(uri)
    secure_cookie = _secure_cookie()
    res.set_cookie('state', state, httponly=True, samesite='Lax', secure=secure_cookie)
    res.set_cookie('cv', code_verifier, httponly=True, samesite='Lax', secure=secure_cookie)

    return res

@auth_bp.get('/callback')
@auth_bucket.consume()
def callback():
    @after_this_request
    def clear_cookies(res_: Response):
        res_.delete_cookie('state')
        res_.delete_cookie('cv')

        return res_

    state = request.cookies.get('state', '', str)
    code_verifier = request.cookies.get('cv', '', str)

    if state == '' or code_verifier == '':
        res = json_error(400)
    else:
        client = OAuth2Session(OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, state=state)

        try:
            client.fetch_token(
                OIDC_TOKEN_ENDPOINT,
                code_verifier=code_verifier,
                authorization_response=request.url,
                timeout=OIDC_TIMEOUT_SECONDS,
            )
        except OAuth2Error:
            abort(400)
        except RequestException:
            abort(502)

        try:
            user_info_req = client.get(OIDC_USERINFO_ENDPOINT, timeout=OIDC_TIMEOUT_SECONDS)
        except RequestException:
            abort(502)

        if user_info_req.status_code != 200:
            res = json_error(400)
        else:
            try:
                user_info = user_info_req.json()
                sub = user_info['sub']
                if not isinstance(sub, str) or sub == '':
                    raise ValueError('OIDC sub claim must be a non-empty string')
            except (KeyError, TypeError, ValueError, RequestException):
                return json_error(502, message='OIDC user info response is invalid')

            db = cast(SASession, g.db)
            existing_user = db.query(User).filter(User.sub == sub).first()
            if existing_user is None:
                try:
                    username = user_info['preferred_username']
                    email = user_info['email']
                    groups = user_info.get('groups', [])
                    if not isinstance(username, str) or username == '':
                        raise ValueError('OIDC preferred_username claim must be a non-empty string')
                    if not isinstance(email, str) or email == '':
                        raise ValueError('OIDC email claim must be a non-empty string')
                    if not isinstance(groups, list) or not all(isinstance(group, str) for group in groups):
                        raise ValueError('OIDC groups claim must be a list of strings')
                except (KeyError, TypeError, ValueError):
                    return json_error(502, message='OIDC user info response is invalid')

                api_key = IDGenerator.generate(64, prefix='api')
                is_admin = bool({'tetra_admin', 'splash_admin'} & set(groups))
                user = User(
                        username=username,
                        sub=sub,
                        email=email,
                        api_key=api_key,
                        admin=is_admin,
                )

                db.add(user)
                db.commit()

            previous_url_cookie = request.cookies.get('previous_url', '', str)
            try:
                previous_url = previous_url_serializer.loads(previous_url_cookie) if previous_url_cookie != '' else ''
            except BadData:
                previous_url = ''

            if previous_url != '' and _is_local_redirect(previous_url):
                res = redirect(previous_url)
                res.delete_cookie('previous_url')
            else:
                res = redirect('/')
                if previous_url_cookie != '':
                    res.delete_cookie('previous_url')

            res.set_cookie(
                'user',
                user_session_serializer.dumps(sub),
                expires=datetime.now(timezone.utc) + timedelta(days=365),
                httponly=True,
                samesite='Lax',
                secure=_secure_cookie()
            )

    return res

@auth_bp.get('/invalidate')
def invalidate():
    res = redirect('/')
    res.delete_cookie('user')

    return res
