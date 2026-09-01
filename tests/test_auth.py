from base64 import b64encode
from types import SimpleNamespace

from flask import g
from authlib.oauth2 import OAuth2Error

from splash import lifecycle
from splash.app import create_app
from splash.serializers import user_session_serializer
from splash.blueprints.auth import _is_local_redirect
from splash.blueprints import auth as auth_blueprint


class _CapturingQuery:
    def __init__(self, captured):
        self.captured = captured

    def filter(self, criterion):
        self.captured.update(criterion.compile().params)

        return self

    def first(self):
        return SimpleNamespace(sub='authenticated')


class _CapturingSession:
    captured = {}

    def query(self, _model):
        return _CapturingQuery(self.captured)

    def close(self):
        pass


def test_redirect_validation_accepts_only_local_paths():
    assert _is_local_redirect('/images/abc?raw=true')
    assert not _is_local_redirect('https://attacker.example/')
    assert not _is_local_redirect('//attacker.example/')
    assert not _is_local_redirect('relative/path')


def test_basic_authorization_takes_precedence_over_session_cookie(monkeypatch):
    _CapturingSession.captured = {}
    monkeypatch.setattr(lifecycle, 'Session', _CapturingSession)
    app = create_app()
    app.add_url_rule('/authenticated-sub', view_func=lambda: g.user.sub)
    client = app.test_client()
    client.set_cookie('user', user_session_serializer.dumps('cookie-sub'))
    credentials = b64encode(b'header-sub:header-key').decode()

    response = client.get('/authenticated-sub', headers={'Authorization': f'bAsIc {credentials}'})

    assert response.text == 'authenticated'
    assert set(_CapturingSession.captured.values()) == {'header-sub', 'header-key'}


def test_failed_oidc_callback_clears_transient_cookies(monkeypatch):
    class FailingOAuthSession:
        def __init__(self, *_args, **_kwargs):
            pass

        def fetch_token(self, *_args, **_kwargs):
            raise OAuth2Error(error='invalid_grant')

    monkeypatch.setattr(auth_blueprint, 'OAuth2Session', FailingOAuthSession)
    client = create_app().test_client()
    client.set_cookie('state', 'expected-state')
    client.set_cookie('cv', 'code-verifier')

    response = client.get(
        '/auth/callback?code=invalid&state=expected-state',
        environ_overrides={'REMOTE_ADDR': '203.0.113.44'},
    )
    response_cookies = response.headers.getlist('Set-Cookie')

    assert response.status_code == 400
    assert any(cookie.startswith('state=;') for cookie in response_cookies)
    assert any(cookie.startswith('cv=;') for cookie in response_cookies)
