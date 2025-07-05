from datetime import datetime
from splash.lib.features import get_feature
from limits import parse, storage, strategies
from flask import request, Response, Blueprint
from splash.http.response import abort_if, json_error
from splash.blueprints.api.features import features_bp

api_bp = Blueprint('api', __name__, url_prefix='/api')
api_bp.register_blueprint(features_bp)

daily_rate_limit_enabled = get_feature('DAILY_RATE_LIMIT_ENABLED')
daily_rate_limit_strategy = strategies.FixedWindowRateLimiter(storage.MemoryStorage())
daily_rate_limit_limiter = parse('10000/day')

@api_bp.before_request
def require_user_agent():
    user_agent = request.user_agent.string.strip()

    abort_if(len(user_agent) < 1, 400)

@api_bp.before_request
def consume_daily_rate_limit():
    if daily_rate_limit_enabled:
        request_ip = request.remote_addr
        allowed = daily_rate_limit_strategy.hit(daily_rate_limit_limiter, request_ip)
        if not allowed:
            window_stats = daily_rate_limit_strategy.get_window_stats(daily_rate_limit_limiter, request_ip)
            expiration_date = datetime.fromtimestamp(window_stats.reset_time)
            return json_error(429, message=f'Daily request limit reached for {request_ip}. Please try again at {expiration_date}.')

    return None

@api_bp.after_request
def add_cors_headers(response: Response):
    response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, PUT, POST, PATCH, DELETE',
    })

    return response
