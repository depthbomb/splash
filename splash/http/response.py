from functools import cache
from http import HTTPStatus
from typing import Union, TypeAlias, Optional, NoReturn
from flask import g, abort, jsonify, url_for, Response, make_response

_SerializablePayload: TypeAlias = Union[dict, list]
_FlaskResponse: TypeAlias = Union[Response, tuple[Response, int]]

RenderedResponse: TypeAlias = Optional[Union[dict, tuple]]

def abort_if(predicate: bool, status_code: int, *, message: Optional[str] = None) -> Optional[NoReturn]:
    if predicate:
        abort(status_code, message)

def abort_unless(predicate: bool, status_code: int, *, message: Optional[str] = None) -> Optional[NoReturn]:
    if not predicate:
        abort(status_code, message)

def json_error(status_code: int, *, message: str = None, headers: Optional[dict[str, str]] = None) -> _FlaskResponse:
    message = message or get_status_code_phrase(status_code)
    return json_response({ 'message': message }, status_code=status_code, headers=headers)

def json_response(data: _SerializablePayload, *, status_code: int = 200, headers: Optional[dict[str, str]] = None) -> _FlaskResponse:
    res = jsonify({
        'request_id': g.request_id,
        'status_code': status_code,
        'result': data
    })
    res.status_code = status_code

    if headers is not None:
        res.headers.update(headers)

    return res

def plaintext_response(text: str, *, status_code: int = 200, headers: dict[str, str] = None) -> _FlaskResponse:
    res = make_response(text)
    res.status_code = status_code
    res.content_type = 'text/plain'

    if headers is not None:
        res.headers.update(headers)

    return res

def deprecated_response(since: str, alternative: Optional[str] = None) -> _FlaskResponse:
    payload = {
        'message': f'This endpoint has been deprecated since {since}. Refer to the API documentation for more info.'
    }

    if alternative:
        payload['alternative'] = url_for(alternative)

    return json_response(payload, status_code=410)

@cache
def get_status_code_phrase(status_code: int) -> str:
    return HTTPStatus(status_code).phrase
