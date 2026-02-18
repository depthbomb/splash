from io import BytesIO
from splash.lib.b2 import bucket
from typing import cast, Optional
from splash import MAX_UPLOAD_SIZE
from splash.db.models import User, Image
from splash.lib.id_generator import IDGenerator
from splash.decorators.common import add_cache_control
from sqlalchemy.orm.session import Session as SASession
from splash.lib.rate_limits import get_or_create_bucket
from splash.decorators.auth import requires_authentication
from flask import g, abort, url_for, request, Blueprint, Response
from splash.http.response import abort_if, abort_unless, json_response
from splash.lib.images import hash_image_bytes, get_image_info_from_bytes

images_bp = Blueprint('images', __name__, url_prefix='/images')
images_bucket = get_or_create_bucket('images', '2/second')

def _get_cached_image(uid: str) -> Optional[Image]:
    image_cache = getattr(g, '_image_cache', None)
    if image_cache is None:
        image_cache = {}
        g._image_cache = image_cache

    if uid in image_cache:
        return cast(Optional[Image], image_cache[uid])

    db = cast(SASession, g.db)
    if '.' in uid:
        name, ext_name = uid.rsplit('.', 1)
        extension = f'.{ext_name}'
        image = db.query(Image).filter((Image.uid == name) & (Image.extension == extension)).first()
    else:
        image = db.query(Image).filter(Image.uid == uid).first()

    image_cache[uid] = image
    return cast(Optional[Image], image)

def _image_etag(uid: str) -> Optional[str]:
    image = _get_cached_image(uid)
    if image is None:
        return None

    return image.sha256

@images_bp.put('/')  # PUT /images
@images_bucket.consume(cost=2)
@requires_authentication()
def upload_image():
    abort_unless('file' in request.files, 400)

    file = request.files['file']
    use_sharex = request.args.get('sharex', 'false').lower() == 'true'
    original_name = file.filename

    file_contents = file.read(MAX_UPLOAD_SIZE + 1)
    size = len(file_contents)

    abort_if(size > MAX_UPLOAD_SIZE, 400, message='Uploaded file must be less than or equal to %d bytes' % MAX_UPLOAD_SIZE)
    is_valid, ext, content_type = get_image_info_from_bytes(file_contents)
    abort_unless(is_valid, 400, message='Uploaded file must be an image')
    abort_unless(ext is not None and content_type is not None, 400, message='Uploaded image format is not supported')

    uid = IDGenerator.generate(8)
    extension = ext
    image_name = f'uploads/{uid}{extension}'
    deletion_key = IDGenerator.generate(64, prefix='delete')
    sha256 = hash_image_bytes(file_contents)

    try:
        bucket.upload_fileobj(BytesIO(file_contents), image_name, ExtraArgs={'ContentType': content_type})

        db = cast(SASession, g.db)
        user = cast(User, g.user)
        image = Image(
                uid=uid,
                original_name=original_name,
                extension=extension,
                content_type=content_type,
                deletion_key=deletion_key,
                size=size,
                sha256=sha256,
                user_id=user.id
        )
        db.add(image)
        db.commit()

        image_url = url_for('images.get_image', uid=f'{uid}{extension}', _external=True)

        if use_sharex:
            return json_response({
                'url': url_for('index.get_image_short', uid=f'{uid}{extension}', _external=True),
                'deletion_url': url_for('images.delete_image', uid=uid, deletion_key=deletion_key, _external=True),
            }, status_code=201)

        return json_response({
            'url': image_url,
            'deletion_key': deletion_key
        }, status_code=201)
    except:
        abort(500)

@images_bp.get('/<string:uid>')  # GET /images/<uid>
@images_bucket.consume()
@add_cache_control(max_age=60 * 60 * 24, etag_getter=_image_etag)
def get_image(uid: str):
    image = _get_cached_image(uid)
    abort_if(not image, 404)
    image = cast(Image, image)

    if '.' in uid:
        key = f'uploads/{uid}'
        obj = bucket.Object(key).get()
        return Response(
                obj['Body'].iter_chunks(chunk_size=8192),
                mimetype=image.content_type,
                headers={
                    'Content-Length': str(obj['ContentLength']),
                }
        )
    else:
        return json_response({
            'original_name': image.original_name,
            'content_type': image.content_type,
            'size': image.size,
            'sha256': image.sha256,
            'created_at': image.created_at,
            'updated_at': image.updated_at,
        })

@images_bp.delete('/<string:uid>/<string:deletion_key>')  # DELETE /images/<uid>/<deletion_key>
@images_bp.get('/<string:uid>/<string:deletion_key>')  # GET /images/<uid>/<deletion_key>
@images_bucket.consume(cost=2)
def delete_image(uid: str, deletion_key: str):
    db = cast(SASession, g.db)
    image = cast(Image, db.query(Image).filter((Image.uid == uid) & (Image.deletion_key == deletion_key)).first())

    abort_if(not image, 404)

    try:
        key = f'uploads/{uid}{image.extension}'
        obj = bucket.Object(key)
        obj.delete()

        db.delete(image)
        db.commit()

        return json_response({})
    except:
        abort(500)
