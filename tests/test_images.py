from io import BytesIO

from PIL import Image
import pytest
from flask import g
from types import SimpleNamespace
from uuid import uuid4

from splash.app import create_app
from splash.lib.images import get_image_info_from_bytes, hash_image_bytes
from splash.blueprints import images as images_blueprint


def _png_bytes() -> bytes:
    output = BytesIO()
    Image.new('RGB', (2, 2), 'red').save(output, format='PNG')
    return output.getvalue()


def test_valid_image_info_and_hash():
    contents = _png_bytes()

    assert get_image_info_from_bytes(contents) == (True, '.png', 'image/png')
    assert len(hash_image_bytes(contents)) == 64


def test_malformed_and_unsupported_images_are_rejected():
    assert get_image_info_from_bytes(b'not an image') == (False, None, None)

    output = BytesIO()
    Image.new('RGB', (2, 2), 'red').save(output, format='BMP')
    assert get_image_info_from_bytes(output.getvalue()) == (False, None, None)


class _FakeSession:
    def __init__(self, events, *, fail_commit=False):
        self.events = events
        self.fail_commit = fail_commit

    def add(self, _):
        self.events.append('db-add')

    def flush(self):
        self.events.append('db-flush')

    def commit(self):
        self.events.append('db-commit')
        if self.fail_commit:
            raise RuntimeError('commit failed')

    def rollback(self):
        self.events.append('db-rollback')

    def close(self):
        self.events.append('db-close')


class _FakeBucket:
    def __init__(self, events):
        self.events = events

    def upload_fileobj(self, *_args, **_kwargs):
        self.events.append('object-upload')

    def Object(self, key):
        events = self.events

        class Object:
            def delete(self):
                events.append(f'object-delete:{key}')

        return Object()


def test_upload_reserves_id_before_object_write_and_compensates_commit_failure(monkeypatch):
    app = create_app()
    events = []
    fake_db = _FakeSession(events, fail_commit=True)
    monkeypatch.setattr(images_blueprint, 'bucket', _FakeBucket(events))
    monkeypatch.setattr(
        images_blueprint.IDGenerator,
        'generate',
        lambda length, prefix=None: 'DELETE-KEY' if prefix == 'delete' else 'IMAGE-ID',
    )

    with app.test_request_context(
        '/images/',
        method='PUT',
        data={'file': (BytesIO(_png_bytes()), 'test.png')},
    ):
        g.db = fake_db
        g.user = SimpleNamespace(id=uuid4())
        with pytest.raises(RuntimeError, match='commit failed'):
            images_blueprint.upload_image.__wrapped__.__wrapped__()

    assert events.index('db-flush') < events.index('object-upload')
    assert 'db-rollback' in events
    assert 'object-delete:uploads/IMAGE-ID.png' in events


def test_download_response_closes_object_body(monkeypatch):
    app = create_app()

    class Body:
        closed = False

        def iter_chunks(self, chunk_size):
            assert chunk_size == 8192
            yield b'image'

        def close(self):
            self.closed = True

    body = Body()

    class Bucket:
        @staticmethod
        def Object(_key):
            return SimpleNamespace(get=lambda: {'Body': body, 'ContentLength': 5})

    monkeypatch.setattr(images_blueprint, 'bucket', Bucket())
    with app.test_request_context('/images/IMAGE-ID.png'):
        g._image_cache = {
            'IMAGE-ID.png': SimpleNamespace(content_type='image/png', sha256='abc')
        }
        response = images_blueprint.get_image.__wrapped__.__wrapped__('IMAGE-ID.png')
        response.close()

    assert body.closed
