from typing import cast
from flask import g, Response, Blueprint
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

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
