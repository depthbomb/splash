from functools import wraps
from typing import cast, Optional
from splash.db.models import User
from splash.http.response import abort_if
from flask import g, request, url_for, redirect
from splash.serializers import previous_url_serializer

def requires_authentication(*, redirect_to_auth = False):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            g.user = cast(Optional[User], g.user)

            if g.user is None:
                if redirect_to_auth:
                    res = redirect(url_for('auth.start_flow'))
                    res.set_cookie('previous_url', previous_url_serializer.dumps(request.url))

                    return res
                else:
                    abort_if(g.user is None, 401)

            return view_func(*args, **kwargs)
        return wrapper
    return decorator
