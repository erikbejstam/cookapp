from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from dotenv import load_dotenv
from functools import wraps
from flask import session, request, redirect, url_for, flash, render_template

import os

load_dotenv()

db = SQLAlchemy()
bcrypt = Bcrypt()

def create_app(test_config=None):
    app = Flask(__name__)

    # A secret for signing session cookies
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

    # Database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqldb://cookapp:bQcmD26UwRwurPA58X4nbz7u4QzzChmE@localhost/cookapp" #os.environ.get("DB_CONNECTION_URL") 
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)
    from . import model

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(model.User, int(user_id))

    # Register blueprints
    # (we import main from here to avoid circular imports in the next lab)
    from . import main

    app.register_blueprint(main.bp)

    from . import auth

    app.register_blueprint(auth.bp)

    return app
