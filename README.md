# Splash

### Developing

- Set up a `venv`
- Run `pip install -r requirements-dev.txt`
- Set the following environment variables:
  - `PORT`
  - `APP_SECRET`
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_ENDPOINT_URL`
  - `AWS_REGION`
  - `AWS_BUCKET_NAME`
  - `DB_HOST`
  - `DB_NAME`
  - `DB_PASS`
  - `DB_PORT`
  - `DB_USER`
  - `OIDC_AUTHORIZE_ENDPOINT`
  - `OIDC_CLIENT_ID`
  - `OIDC_CLIENT_SECRET`
  - `OIDC_TOKEN_ENDPOINT`
  - `OIDC_USERINFO_ENDPOINT`
- Run `yoyo apply --batch` to apply database migrations
- Start the development server with `python -m flask --app dev.py run` and the `FLASK_DEBUG=1` environment variable set to enable code reloading
