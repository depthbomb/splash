from typing import cast
from sqlalchemy import text
from sqlalchemy.orm import Session
from flask import g, Response, Blueprint
from sqlalchemy.exc import SQLAlchemyError

health_bp = Blueprint('health', __name__, url_prefix='/health')

@health_bp.get('')
def health() -> Response:
    return Response(status=204)

@health_bp.get('/ready')
def ready() -> Response:
    try:
        cast(Session, g.db).execute(text('SELECT 1'))
    except SQLAlchemyError:
        return Response(status=503)

    return Response(status=204)
