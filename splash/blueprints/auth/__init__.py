from typing import cast
from splash.db.models import User
from authlib.oauth2 import OAuth2Error
from datetime import datetime, timedelta
from splash.http.response import json_error
from splash.lib.id_generator import IDGenerator
from authlib.common.security import generate_token
from splash.serializers import previous_url_serializer
from sqlalchemy.orm.session import Session as SASession
from splash.lib.rate_limits import get_or_create_bucket
from authlib.integrations.requests_client import OAuth2Session
from flask import g, abort, url_for, request, redirect, Response, Blueprint, after_this_request
from splash.env import OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, OIDC_TOKEN_ENDPOINT, OIDC_USERINFO_ENDPOINT, OIDC_AUTHORIZE_ENDPOINT

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
auth_bucket = get_or_create_bucket('auth', '1/second')

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
    res.set_cookie('state', state, httponly=True, samesite='Lax')
    res.set_cookie('cv', code_verifier, httponly=True, samesite='Lax')

    return res

@auth_bp.get('/callback')
@auth_bucket.consume()
def callback():
    state = request.cookies.get('state', '', str)
    code_verifier = request.cookies.get('cv', '', str)

    if state == '' or code_verifier == '':
        res = json_error(400)
    else:
        client = OAuth2Session(OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, state=state)

        try:
            client.fetch_token(OIDC_TOKEN_ENDPOINT, code_verifier=code_verifier, authorization_response=request.url)
        except OAuth2Error:
            abort(500)

        user_info_req = client.get(OIDC_USERINFO_ENDPOINT)

        if user_info_req.status_code != 200:
            res = json_error(400)
        else:
            db = cast(SASession, g.db)

            user_info = user_info_req.json()
            existing_user = db.query(User).filter(User.sub == user_info['sub']).first()
            if existing_user is None:
                api_key = IDGenerator.generate(64, prefix='api')
                is_admin = any(['tetra_admin' in grp or 'splash_admin' in grp for grp in cast(list[str], user_info['groups'])])
                user = User(
                        username=user_info['preferred_username'],
                        sub=user_info['sub'],
                        email=user_info['email'],
                        api_key=api_key,
                        admin=is_admin,
                )

                db.add(user)
                db.commit()

            previous_url = previous_url_serializer.loads(request.cookies.get('previous_url', '', str))
            if previous_url != '':
                res = redirect(previous_url)
                res.delete_cookie('previous_url')
            else:
                res = redirect('/')

            res.set_cookie('user', user_info['sub'], expires=datetime.now() + timedelta(days=365))

    @after_this_request
    def clear_cookies(res_: Response):
        res_.delete_cookie('state')
        res_.delete_cookie('cv')

        return res_

    return res

@auth_bp.get('/invalidate')
def invalidate():
    res = redirect('/')
    res.set_cookie('user', '', expires=0)

    return res
