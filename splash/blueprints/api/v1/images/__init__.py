from typing import cast
from splash.db import Session
from splash.lib.b2 import bucket
from splash import MAX_UPLOAD_SIZE
from splash.db.models import User, Image
from splash.lib.id_generator import IDGenerator
from splash.decorators.common import add_cache_control
from sqlalchemy.orm.session import Session as SASession
from splash.lib.rate_limits import get_or_create_bucket
from splash.lib.images import hash_image, get_image_info
from splash.decorators.auth import requires_authentication
from flask import g, abort, url_for, request, Blueprint, Response
from splash.http.response import abort_if, abort_unless, json_response

images_bp = Blueprint('images', __name__, url_prefix='/images')
images_bucket = get_or_create_bucket('images', '2/second')

@images_bp.put('/')  # PUT /api/v1/images
@images_bucket.consume(cost=2)
@requires_authentication()
def upload_image():
    abort_unless('file' in request.files, 400)

    file = request.files['file']
    use_sharex = request.args.get('sharex', 'false').lower() == 'true'

    is_valid, ext, content_type = get_image_info(file)

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)

    abort_if(size > MAX_UPLOAD_SIZE, 400, message='Uploaded file must be less than or equal to %d bytes' % MAX_UPLOAD_SIZE)
    abort_unless(is_valid, 400, message='Uploaded file must be an image')

    uid = IDGenerator.generate(8)
    image_name = f'uploads/{uid}{ext}'
    original_name = file.filename
    extension = ext
    deletion_key = IDGenerator.generate(64, prefix='delete')
    sha256 = hash_image(file)

    try:
        bucket.upload_fileobj(file, image_name, ExtraArgs={'ContentType': content_type})

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

        image_url = url_for('api.v1.images.get_image', uid=f'{uid}{ext}', _external=True)

        if use_sharex:
            return json_response({
                'url': url_for('index.get_image_short', uid=f'{uid}{ext}', _external=True),
                'deletion_url': url_for('api.v1.images.delete_image', uid=uid, deletion_key=deletion_key, _external=True),
            }, status_code=201)

        return json_response({
            'url': image_url,
            'deletion_key': deletion_key
        }, status_code=201)
    except:
        abort(500)

@images_bp.get('/<string:uid>')  # GET /api/v1/<uid>
@images_bucket.consume()
@add_cache_control(max_age=60 * 60 * 24)
def get_image(uid: str):
    db = cast(SASession, g.db)
    if '.' in uid:
        name, ext_name = uid.rsplit('.', 1)
        extension = f'.{ext_name}'
        image = cast(Image, db.query(Image).filter((Image.uid == name) & (Image.extension == extension)).first())

        abort_if(not image, 404)

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
        image = db.query(Image).filter(Image.uid == uid).first()

        abort_if(not image, 404)

        return json_response({
            'original_name': image.original_name,
            'content_type': image.content_type,
            'size': image.size,
            'sha256': image.sha256,
            'created_at': image.created_at,
            'updated_at': image.updated_at,
        })

@images_bp.delete('/<string:uid>/<string:deletion_key>')  # DELETE /api/v1/<uid>/<deletion_key>
@images_bp.get('/<string:uid>/<string:deletion_key>')  # GET /api/v1/<uid>/<deletion_key>
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
