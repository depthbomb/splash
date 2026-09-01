from flask import jsonify, request

from splash.app import create_app
from splash.db import engine


def test_app_factory_is_repeatable_and_bare_context_tears_down():
    first = create_app()
    second = create_app()

    with first.app_context():
        pass

    assert second is not first


def test_database_url_preserves_reserved_password_characters():
    assert engine.url.password == 'p@ss:/%word'


def test_proxy_headers_are_honored_for_exactly_one_trusted_hop():
    app = create_app()
    app.add_url_rule('/test-ip', view_func=lambda: request.remote_addr)

    response = app.test_client().get(
        '/test-ip',
        headers={
            'X-Forwarded-For': '198.51.100.10, 10.0.0.2',
            'X-Forwarded-Proto': 'https',
        },
    )

    assert response.text == '10.0.0.2'


def test_feature_admin_secret_is_accepted_only_in_header():
    client = create_app().test_client()

    query_response = client.get('/api/_features?secret=test-app-secret')
    header_response = client.get('/api/_features', headers={'X-App-Secret': 'test-app-secret'})

    assert query_response.status_code == 401
    assert header_response.status_code == 200


def test_untrusted_host_is_rejected():
    response = create_app().test_client().get('/health', base_url='http://attacker.example')

    assert response.status_code == 400


def test_delete_capability_get_route_is_absent():
    response = create_app().test_client().get('/images/image-id/delete-key')

    assert response.status_code == 404


def test_json_provider_supports_keyword_payloads():
    app = create_app()
    app.add_url_rule('/json-keywords', view_func=lambda: jsonify(answer=42))

    response = app.test_client().get('/json-keywords')

    assert response.status_code == 200
    assert response.get_json() == {'answer': 42}
