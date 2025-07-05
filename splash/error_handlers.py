from loguru import logger
from http import HTTPStatus
from functools import partial
from flask import Flask, Response
from typing import cast, Optional
from splash.http.response import json_error
from werkzeug.exceptions import HTTPException  # noqa

def register_error_handlers(app: Flask) -> None:
    """
    Registers handlers for common HTTP status codes and exceptions
    :param app: Flask instance
    """
    def _handle_error(e: Exception, status_code: Optional[int] = None) -> Response:
        status_code = cast(int, status_code or e.code if isinstance(e, HTTPException) else 500)
        message = e.description if hasattr(e, 'description') else HTTPStatus(status_code).phrase

        if app.debug or status_code == 500:
            logger.exception(e)

        return json_error(status_code, message=message)

    for code in [400, 401, 403, 404, 405, 410, 412, 413, 415, 418, 422, 428, 429, 451, 500, 501, 503]:
        app.register_error_handler(code, partial(_handle_error, status_code=code))

        logger.trace('Registered handler for HTTP %d' % code)

    app.register_error_handler(Exception, _handle_error)

    logger.trace('Registered generic exception handler')
