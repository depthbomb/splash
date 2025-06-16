from time import time
from threading import Lock
from functools import wraps
from typing import Optional
from flask import g, request
from splash.http.response import json_error
from limits import parse, RateLimitItem
from limits.storage import MemoryStorage
from splash.lib.id_generator import IDGenerator
from limits.strategies import FixedWindowRateLimiter

_BUCKETS = {}
__LOCK = Lock()

class RateLimitBucket:
    _id: str
    _limit: str
    _cost: int
    _daily: bool
    _limiter: RateLimitItem
    _storage: MemoryStorage
    _strategy: FixedWindowRateLimiter

    def __init__(self, limit: str, *, cost: int = 1, daily: bool = False):
        self._id = IDGenerator.generate(16, prefix='bucket')
        self._limit = limit
        self._cost = cost
        self._daily = daily
        self._limiter = parse(limit)
        self._storage = MemoryStorage()
        self._strategy = FixedWindowRateLimiter(self._storage)

    def consume(self, *, cost: Optional[int] = None):
        cost = cost or self._cost

        def decorator(view_func):
            @wraps(view_func)
            def wrapper(*args, **kwargs):
                id_ = request.remote_addr
                allowed = self._strategy.hit(self._limiter, id_, cost=cost)
                stats = self._strategy.get_window_stats(self._limiter, id_)

                g.ratelimit_limit = self._limiter.amount
                g.ratelimit_cost = cost
                g.ratelimit_remaining = stats.remaining
                g.ratelimit_reset = stats.reset_time
                g.ratelimit_reset_after = round(stats.reset_time - time())
                g.ratelimit_bucket = self._id
                g.ratelimit_active = True

                if not allowed:
                    return json_error(429)

                return view_func(*args, **kwargs)
            return wrapper
        return decorator

def get_or_create_bucket(name: str, limit: str, *, cost: int = 1) -> RateLimitBucket:
    with __LOCK:
        if name in _BUCKETS:
            return _BUCKETS[name]

        new_bucket = RateLimitBucket(limit, cost=cost)
        _BUCKETS[name] = new_bucket

        return new_bucket
