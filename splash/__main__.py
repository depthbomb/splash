from waitress import serve
from splash.env import PORT
from splash.app import create_app
from logging import ERROR, getLogger

logger = getLogger('waitress')
logger.setLevel(ERROR)

serve(create_app(), listen=f'*:{PORT}', ident='Splash Production Server', threads=16)
