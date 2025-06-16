from os import getenv

PORT = getenv('PORT', '8000')

APP_SECRET = getenv('APP_SECRET', '')

DB_USER = getenv('DB_USER', 'postgres')
DB_PASS = getenv('DB_PASS', '1234')
DB_HOST = getenv('DB_HOST', 'localhost')
DB_PORT = getenv('DB_PORT', '5432')
DB_NAME = getenv('DB_NAME', 'splash_dev')

AWS_ACCESS_KEY_ID = getenv('AWS_ACCESS_KEY_ID', '')
AWS_BUCKET_NAME = getenv('AWS_BUCKET_NAME', 'splash-dev')
AWS_ENDPOINT_URL = getenv('AWS_ENDPOINT_URL', 'https://s3.us-west-000.backblazeb2.com')
AWS_REGION = getenv('AWS_REGION', 'us-west-000')
AWS_SECRET_ACCESS_KEY = getenv('AWS_SECRET_ACCESS_KEY', '')

OIDC_CLIENT_ID = getenv('OIDC_CLIENT_ID', '')
OIDC_CLIENT_SECRET = getenv('OIDC_CLIENT_SECRET', '')
OIDC_AUTHORIZE_ENDPOINT = getenv('OIDC_AUTHORIZE_ENDPOINT', 'https://auth.super.fish/application/o/authorize/')
OIDC_TOKEN_ENDPOINT = getenv('OIDC_TOKEN_ENDPOINT', 'https://auth.super.fish/application/o/token/')
OIDC_USERINFO_ENDPOINT = getenv('OIDC_USERINFO_ENDPOINT', 'https://auth.super.fish/application/o/userinfo/')
