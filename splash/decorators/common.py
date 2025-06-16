from typing import Optional
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

def add_cache_control(*, max_age: int = 60):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if request.headers.get('If-None-Match'):
                res = make_response(view_func(*args, **kwargs))
                res.cache_control.public = True
                res.cache_control.max_age = max_age
                res.add_etag()
                return res.make_conditional(request)

            res = make_response(view_func(*args, **kwargs))
            res.cache_control.public = True
            res.cache_control.max_age = max_age
            res.add_etag()
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
