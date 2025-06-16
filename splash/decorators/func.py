from sys import maxsize
from functools import wraps
from datetime import datetime

def cache(ttl: int = maxsize):
    def decorator(func):
        cache_data = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = datetime.now()
            func_name = func.__name__ + str(args) + str(kwargs)
            if func_name in cache_data and (current_time - cache_data[func_name]['t']).total_seconds() < ttl:
                result = cache_data[func_name]['r']
            else:
                result = func(*args, **kwargs)
                cache_data[func_name] = {'r': result, 't': current_time}

            return result
        return wrapper
    return decorator
