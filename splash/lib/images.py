from PIL import Image
from hashlib import sha256
from typing import Optional
from werkzeug.datastructures import FileStorage  # noqa

_FORMAT_TO_EXTENSION = {
    'JPEG': '.jpg',
    'PNG': '.png',
    'GIF': '.gif',
    'WEBP': '.webp',
}

def get_image_info(file_obj: FileStorage) -> tuple[bool, Optional[str], Optional[str]]:
    try:
        file_obj.seek(0)
        with Image.open(file_obj) as img:
            img.verify()
            extension = _FORMAT_TO_EXTENSION.get(img.format)

        file_obj.seek(0)
        return True, extension, img.get_format_mimetype()
    except:
        return False, None, None

def hash_image(file_obj: FileStorage) -> str:
    sha256_hash = sha256()
    while True:
        chunk = file_obj.read(8192)
        if not chunk:
            break
        sha256_hash.update(chunk)

    file_obj.seek(0)

    return sha256_hash.hexdigest()
