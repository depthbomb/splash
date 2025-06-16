from flask import Response, Blueprint

health_bp = Blueprint('health', __name__, url_prefix='/health')

@health_bp.get('')
def health() -> Response:
    return Response(status=204)
