from PIL import Image
from io import BytesIO
from hashlib import sha256
from typing import Optional
from splash import MAX_PIXEL_SIZE
from werkzeug.datastructures import FileStorage  # noqa

Image.MAX_IMAGE_PIXELS = MAX_PIXEL_SIZE

_FORMAT_TO_EXTENSION = {
    'JPEG': '.jpg',
    'PNG': '.png',
    'GIF': '.gif',
    'WEBP': '.webp',
}

def get_image_info(file_obj: FileStorage) -> tuple[bool, Optional[str], Optional[str]]:
    try:
        file_obj.seek(0)
        contents = file_obj.read()
        return get_image_info_from_bytes(contents)
    finally:
        file_obj.seek(0)

def get_image_info_from_bytes(contents: bytes) -> tuple[bool, Optional[str], Optional[str]]:
    try:
        with Image.open(BytesIO(contents)) as img:
            img.verify()
            image_format = img.format

        extension = _FORMAT_TO_EXTENSION.get(image_format)
        content_type = Image.MIME.get(image_format) if image_format is not None else None
        if image_format is None or extension is None or content_type is None:
            return False, None, None

        return True, extension, content_type
    except:
        return False, None, None

def hash_image(file_obj: FileStorage) -> str:
    try:
        file_obj.seek(0)
        return hash_image_bytes(file_obj.read())
    finally:
        file_obj.seek(0)

def hash_image_bytes(contents: bytes) -> str:
    return sha256(contents).hexdigest()
