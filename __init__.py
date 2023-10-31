from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__)

    # A secret for signing session cookies
    app.config["SECRET_KEY"] = "93220d9b340cf9a6c39bac99cce7daf220167498f91fa"

    # Register blueprints
    # (we import main from here to avoid circular imports in the next lab)
    from . import main

    app.register_blueprint(main.bp)
    return app
