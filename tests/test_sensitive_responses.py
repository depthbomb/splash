from types import SimpleNamespace

from splash import lifecycle
from splash.app import create_app


class _UserQuery:
    def filter(self, _criterion):
        return self

    def first(self):
        return SimpleNamespace(
            username='test-user',
            sub='test-sub',
            api_key='test-api-key',
        )


class _UserSession:
    def query(self, _model):
        return _UserQuery()

    def close(self):
        pass


def test_responses_containing_credentials_are_never_cached(monkeypatch):
    monkeypatch.setattr(lifecycle, 'Session', _UserSession)
    client = create_app().test_client()

    index_response = client.get('/?api_key=test-api-key')
    sharex_response = client.get('/sharex?api_key=test-api-key')

    assert index_response.cache_control.no_store
    assert sharex_response.cache_control.no_store
    assert not index_response.cache_control.public
    assert not sharex_response.cache_control.public
