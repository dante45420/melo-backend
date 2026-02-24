"""Factory de la aplicación Flask."""
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config_name=None):
    """Crear y configurar la aplicación."""
    from config import config
    import os

    env = config_name or os.environ.get('FLASK_ENV', 'development')
    app = Flask(__name__)
    app.config.from_object(config[env])

    # Render usa DATABASE_URL con postgres://; SQLAlchemy 1.4+ requiere postgresql://
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
    if db_url and db_url.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace('postgres://', 'postgresql://', 1)

    CORS(app, origins=['*'], supports_credentials=True)
    db.init_app(app)

    from app.routes import register_routes
    register_routes(app)

    with app.app_context():
        db.create_all()

    return app
