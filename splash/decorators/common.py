from typing import Optional, Callable
from functools import wraps
from flask import request, url_for, Response, make_response

def deprecated(removed_in: str, *, alternative_endpoint: Optional[str] = None):
    """
    Adds a deprecation notice to the response headers of endpoints to warn that the endpoint has been deprecated.
    :param removed_in: The version in which the endpoint will be removed.
    :param alternative_endpoint: The optional, alternative route name the user should use instead.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            res = view_func(*args, **kwargs)
            if not isinstance(res, Response):
                res = make_response(res)

            res.headers.add_header('Deprecated', f'This endpoint has been deprecated and will be removed in {removed_in}. Refer to the API documentation for more info.')

            if alternative_endpoint is not None:
                res.headers.add_header('Deprecated-Alternative', url_for(alternative_endpoint))

            return res
        return wrapper
    return decorator

def add_cache_control(*, max_age: int = 60, etag_getter: Optional[Callable[..., Optional[str]]] = None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            supports_conditional = request.method in ('GET', 'HEAD')
            etag = etag_getter(*args, **kwargs) if etag_getter is not None else None

            if supports_conditional and etag is not None and request.if_none_match.contains(etag):
                res = make_response('', 304)
                res.cache_control.public = True
                res.cache_control.max_age = max_age
                res.set_etag(etag)
                return res

            res = make_response(view_func(*args, **kwargs))
            res.cache_control.public = True
            res.cache_control.max_age = max_age

            if etag is not None:
                res.set_etag(etag)
            elif not res.get_etag()[0]:
                res.add_etag()

            if supports_conditional:
                return res.make_conditional(request)

            return res
        return wrapper
    return decorator

def no_cache_control(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        res = make_response(view_func(*args, **kwargs))
        res.cache_control.no_store = True
        return res

    return wrapper
