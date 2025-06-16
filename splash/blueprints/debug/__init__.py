from flask import abort, Blueprint

debug_bp = Blueprint('debug', __name__, url_prefix='/debug')

@debug_bp.get('/status_code/<int:code>')
def debug_send_status_code(code: int):
    abort(code)
