import os
from flask import Flask
from flask_cors import CORS

from config import get_database_uri
from app.extensions import db, migrate
from app.auth.routes import auth_bp


def create_app():
    flask_app = Flask(__name__)
    flask_app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    frontend_urls = os.environ.get("FRONTEND_URL", "http://localhost:5173").split(",")
    CORS(flask_app, origins=[u.strip() for u in frontend_urls], supports_credentials=True)

    flask_app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    if os.environ.get("FLASK_ENV") == "production":
        flask_app.config["SESSION_COOKIE_SECURE"] = True
        flask_app.config["SESSION_COOKIE_SAMESITE"] = "None"

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)

    with flask_app.app_context():
        import app.models  # noqa: F401

    flask_app.register_blueprint(auth_bp)

    from app.api import register_api_blueprints
    register_api_blueprints(flask_app)

    return flask_app
