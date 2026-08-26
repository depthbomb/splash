from pathlib import Path

from yoyo import get_backend, read_migrations

from splash.db import DATABASE_URL


MIGRATIONS_PATH = Path(__file__).resolve().parent.parent / 'migrations'


def main() -> None:
    database_url = DATABASE_URL.render_as_string(hide_password=False)
    backend = get_backend(database_url)
    migrations = read_migrations(str(MIGRATIONS_PATH))

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))


if __name__ == '__main__':
    main()
