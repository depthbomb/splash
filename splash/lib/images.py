from PIL import Image
from io import BytesIO
from splash import MAX_PIXEL_SIZE
from typing import BinaryIO, Optional
from hashlib import sha256, file_digest
from werkzeug.datastructures import FileStorage

Image.MAX_IMAGE_PIXELS = MAX_PIXEL_SIZE

_FORMAT_TO_EXTENSION = {
    'JPEG': '.jpg',
    'PNG': '.png',
    'GIF': '.gif',
    'WEBP': '.webp',
}

def _get_verified_image_info(file_obj: BinaryIO) -> tuple[bool, Optional[str], Optional[str]]:
    with Image.open(file_obj) as image:
        width, height = image.size
        if width * height > MAX_PIXEL_SIZE:
            return False, None, None

        image_format = image.format
        image.verify()

    extension = _FORMAT_TO_EXTENSION.get(image_format)
    content_type = Image.MIME.get(image_format) if image_format is not None else None
    if image_format is None or extension is None or content_type is None:
        return False, None, None

    return True, extension, content_type

def get_image_info(file_obj: FileStorage) -> tuple[bool, Optional[str], Optional[str]]:
    try:
        file_obj.seek(0)

        return _get_verified_image_info(file_obj.stream)
    except Exception:
        return False, None, None
    finally:
        file_obj.seek(0)

def get_image_info_from_bytes(contents: bytes) -> tuple[bool, Optional[str], Optional[str]]:
    try:
        return _get_verified_image_info(BytesIO(contents))
    except Exception:
        return False, None, None

def hash_image(file_obj: FileStorage) -> str:
    try:
        file_obj.seek(0)

        digest = file_digest(file_obj.stream, 'sha256')

        return digest.hexdigest()
    finally:
        file_obj.seek(0)

def hash_image_bytes(contents: bytes) -> str:
    return sha256(contents).hexdigest()
