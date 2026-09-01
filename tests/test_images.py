from io import BytesIO

from PIL import Image
import pytest
from flask import g
from werkzeug.datastructures import FileStorage
from types import SimpleNamespace
from uuid import uuid4

from splash.app import create_app
from splash import MAX_PIXEL_SIZE
from splash.lib.images import get_image_info, get_image_info_from_bytes, hash_image, hash_image_bytes
from splash.blueprints import images as images_blueprint


def _png_bytes() -> bytes:
    output = BytesIO()
    Image.new('RGB', (2, 2), 'red').save(output, format='PNG')
    return output.getvalue()


def test_valid_image_info_and_hash():
    contents = _png_bytes()

    assert get_image_info_from_bytes(contents) == (True, '.png', 'image/png')
    assert len(hash_image_bytes(contents)) == 64

    storage = FileStorage(stream=BytesIO(contents), filename='test.png')
    assert get_image_info(storage) == (True, '.png', 'image/png')
    assert hash_image(storage) == hash_image_bytes(contents)
    assert storage.tell() == 0


def test_malformed_and_unsupported_images_are_rejected():
    assert get_image_info_from_bytes(b'not an image') == (False, None, None)

    output = BytesIO()
    Image.new('RGB', (2, 2), 'red').save(output, format='BMP')
    assert get_image_info_from_bytes(output.getvalue()) == (False, None, None)


def test_images_over_the_exact_pixel_limit_are_rejected(monkeypatch):
    class OversizedImage:
        size = (MAX_PIXEL_SIZE + 1, 1)
        format = 'PNG'

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def verify(self):
            raise AssertionError('oversized image contents should not be processed')

    monkeypatch.setattr('splash.lib.images.Image.open', lambda _stream: OversizedImage())

    assert get_image_info_from_bytes(b'image header') == (False, None, None)


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


def test_upload_cleans_up_a_partially_written_object(monkeypatch):
    class FailingBucket(_FakeBucket):
        def upload_fileobj(self, *_args, **_kwargs):
            self.events.append('object-upload-started')
            raise RuntimeError('upload interrupted')

    app = create_app()
    events = []
    fake_db = _FakeSession(events)
    monkeypatch.setattr(images_blueprint, 'bucket', FailingBucket(events))
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
        with pytest.raises(RuntimeError, match='upload interrupted'):
            images_blueprint.upload_image.__wrapped__.__wrapped__()

    assert 'db-rollback' in events
    assert 'object-delete:uploads/IMAGE-ID.png' in events


def test_download_response_closes_object_body(monkeypatch):
    app = create_app()

    class Body:
        closed = False

        def iter_chunks(self, chunk_size):
            assert chunk_size == images_blueprint.DOWNLOAD_CHUNK_SIZE
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


def test_head_request_uses_object_metadata_without_opening_body(monkeypatch):
    events = []

    class BucketObject:
        content_length = 5

        def load(self):
            events.append('object-head')

        def get(self):
            raise AssertionError('HEAD must not open an object body')

    class Bucket:
        @staticmethod
        def Object(_key):
            return BucketObject()

    app = create_app()
    monkeypatch.setattr(images_blueprint, 'bucket', Bucket())
    with app.test_request_context('/images/IMAGE-ID.png', method='HEAD'):
        g._image_cache = {
            'IMAGE-ID.png': SimpleNamespace(content_type='image/png', sha256='abc')
        }
        response = images_blueprint.get_image.__wrapped__.__wrapped__('IMAGE-ID.png')

    assert response.status_code == 200
    assert response.content_length == 5
    assert events == ['object-head']
