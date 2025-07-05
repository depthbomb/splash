from flask import Flask

def register_blueprints(app: Flask) -> None:
    # Import the blueprints locally so feature flags can be checked in the top-level of blueprints
    from splash.blueprints.api import api_bp
    from splash.blueprints.auth import auth_bp
    from splash.blueprints.index import index_bp
    from splash.blueprints.health import health_bp
    from splash.blueprints.images import images_bp
    from splash.blueprints.sharex import sharex_bp

    app.register_blueprint(index_bp, app=app)
    app.register_blueprint(auth_bp, app=app)
    app.register_blueprint(images_bp, app=app)
    app.register_blueprint(sharex_bp, app=app)
    app.register_blueprint(api_bp, app=app)
    app.register_blueprint(health_bp, app=app)

    if app.debug:
        from splash.blueprints.debug import debug_bp
        app.register_blueprint(debug_bp, app=app)
