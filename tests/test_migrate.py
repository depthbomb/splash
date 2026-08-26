from contextlib import nullcontext
from urllib.parse import urlsplit

from splash import migrate


class _Backend:
    def __init__(self):
        self.applied = None

    def lock(self):
        return nullcontext()

    def to_apply(self, migrations):
        return ['pending', migrations]

    def apply_migrations(self, migrations):
        self.applied = migrations


def test_migration_entrypoint_encodes_database_credentials(monkeypatch):
    backend = _Backend()
    captured = {}
    monkeypatch.setattr(migrate, 'get_backend', lambda url: captured.setdefault('url', url) and backend)
    monkeypatch.setattr(migrate, 'read_migrations', lambda path: ['migration', path])

    migrate.main()

    parsed = urlsplit(captured['url'])
    assert parsed.password == 'p%40ss%3A%2F%25word'
    assert backend.applied[0] == 'pending'
    assert backend.applied[1][0] == 'migration'
