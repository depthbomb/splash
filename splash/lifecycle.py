from typing import cast
from loguru import logger
from sqlalchemy import or_
from base64 import b64decode
from splash.db import Session
from splash.db.models import User
from itsdangerous import BadSignature
from splash.lib.features import get_feature
from splash.lib.id_generator import IDGenerator
from splash.serializers import user_session_serializer
from sqlalchemy.orm.session import Session as SASession
from flask import g, abort, Flask, request, Response, after_this_request

def register_lifecycle_hooks(app: Flask) -> None:
    maintenance_mode = get_feature('MAINTENANCE_MODE_ENABLED')

    @app.before_request
    def init_globals():
        """
        Initializes global values, for example the database session.
        """
        g.db = Session()
        g.user = None
        g.ratelimit_active = False

    @app.before_request
    def generate_request_id():
        """
        Generates a unique request ID and applies it to the response.
        """
        g.request_id = IDGenerator.generate(12, prefix='req')

        @after_this_request
        def add_request_id_header(res: Response):
            res.headers.add_header('X-Request-Id', g.request_id)

            return res

    @app.before_request
    def check_for_maintenance():
        """
        Checks for the maintenance mode feature flag being enabled and returns an HTTP 503 response on all routes
        except for the features namespace.
        """
        if maintenance_mode and not request.path.startswith('/api/_features'):
            abort(503)

    @app.before_request
    def load_user():
        """
        Attempts to load user data and attach it to the request context. The user is loaded either by checking the
        `?api_key` query parameter, the `user` cookie value, or the `Authorization` header.
        """

        api_key = request.args.get('api_key')
        cookie = request.cookies.get('user')
        auth_header = request.headers.get('Authorization')

        if api_key or cookie or auth_header:
            db = cast(SASession, g.db)
            filters = []
            if api_key:
                filters.append(User.api_key == api_key)
            elif cookie:
                try:
                    cookie_sub = user_session_serializer.loads(cookie)
                    filters.append(User.sub == cookie_sub)
                except BadSignature:
                    pass
            elif auth_header and auth_header.startswith('Basic '):
                try:
                    encoded_credentials = auth_header.split(' ', 1)[1]
                    decoded_credentials = b64decode(encoded_credentials).decode('utf-8')
                    sub, basic_api_key = decoded_credentials.split(':', 1)
                    filters.append(
                        (User.sub == sub) & (User.api_key == basic_api_key)
                    )
                except (ValueError, UnicodeDecodeError, IndexError):
                    pass

            if filters:
                g.user = db.query(User).filter(or_(*filters)).first()

    @app.before_request
    def log_request() -> None:
        """
        Logs info about the incoming request and its response.
        """
        request_id = g.request_id
        request_ip = request.remote_addr
        request_path = request.path
        request_method = request.method

        logger.debug('[%s] %s -> %s %s' % (request_id, request_ip, request_method, request_path))

        @after_this_request
        def log_response(res: Response):
            status = res.status
            content_type = res.content_type
            logger.debug('[%s] %s <- %s %s' % (request_id, request_ip, status, content_type))

            return res

    @app.after_request
    def add_last_headers(res: Response):
        """
        Adds any remaining required headers to the response, particularly rate limit-related ones.
        """
        if bool(g.ratelimit_active):
            headers = {
                'X-RateLimit-Limit': str(g.ratelimit_limit),
                'X-RateLimit-Cost': str(g.ratelimit_cost),
                'X-RateLimit-Remaining': str(g.ratelimit_remaining),
                'X-RateLimit-Reset': str(g.ratelimit_reset),
                'X-RateLimit-Reset-After': str(g.ratelimit_reset_after),
                'X-RateLimit-Bucket': g.ratelimit_bucket,
            }
            res.headers.update(headers)

        return res

    @app.teardown_appcontext
    def teardown(_):
        cast(SASession, g.db).close()
