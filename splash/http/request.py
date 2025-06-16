from flask import request, Request
from typing import Union, Optional
from werkzeug.datastructures.structures import ImmutableMultiDict  # noqa

def get_form_payload(req: Optional[Request] = None) -> ImmutableMultiDict[str, str]:
    """
    Returns the request payload for `application/json` or `application/x-www-form-urlencoded` content types.
    :param req: Optional Flask request
    """
    if req is None:
        req = request

    return req.json if req.is_json else req.form


def get_plaintext_payload(req: Optional[Request] = None) -> Optional[str]:
    """
    Returns the request payload for the `text/plain` content type.
    :param req: Optional Flask request
    """
    if req is None:
        req = request

    if not req.mimetype or not req.mimetype.startswith('text/plain'):
        return None

    return req.data.decode('utf-8')


def get_request_payload(req: Optional[Request] = None) -> Optional[Union[ImmutableMultiDict[str, str], str]]:
    """
    Returns the request data payload.

    This can return either `str` if the request is `text/plain` or an `ImmutableMultiDict[str, str]` if the request is
    `application/json` or `application/x-www-form-urlencoded`.
    :param req: Optional Flask request
    """
    if req is None:
        req = request

    return get_plaintext_payload(req) or get_form_payload(req)
