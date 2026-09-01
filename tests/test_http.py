from flask import Flask

from splash.decorators.common import add_cache_control
from splash.http.request import get_request_payload


def test_empty_plaintext_payload_remains_plaintext():
    app = Flask(__name__)

    with app.test_request_context('/', method='POST', data=b'', content_type='text/plain'):
        assert get_request_payload() == ''


def test_weak_if_none_match_avoids_rendering_matching_resource():
    app = Flask(__name__)
    calls = []

    @app.get('/resource')
    @add_cache_control(etag_getter=lambda: 'content-hash')
    def resource():
        calls.append('rendered')

        return 'body'

    response = app.test_client().get('/resource', headers={'If-None-Match': 'W/"content-hash"'})

    assert response.status_code == 304
    assert response.headers['ETag'] == '"content-hash"'
    assert calls == []
