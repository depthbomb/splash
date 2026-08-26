from sqlalchemy.exc import OperationalError

from splash.app import create_app
from splash import lifecycle


class _FakeSession:
    def __init__(self, error=None):
        self.error = error

    def execute(self, _statement):
        if self.error is not None:
            raise self.error

    def close(self):
        pass


def test_readiness_succeeds_when_database_responds(monkeypatch):
    monkeypatch.setattr(lifecycle, 'Session', _FakeSession)

    assert create_app().test_client().get('/health/ready').status_code == 204


def test_readiness_fails_when_database_is_unavailable(monkeypatch):
    error = OperationalError('SELECT 1', {}, RuntimeError('unavailable'))
    monkeypatch.setattr(lifecycle, 'Session', lambda: _FakeSession(error))

    assert create_app().test_client().get('/health/ready').status_code == 503
