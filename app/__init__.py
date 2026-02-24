"""Factory de la aplicación Flask."""
from flask import Flask, request, jsonify
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

    db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
    if db_url and isinstance(db_url, str) and db_url.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://' + db_url[11:]

    # CORS: orígenes permitidos (frontend en Vercel). En dev: localhost.
    origins = app.config.get('CORS_ORIGINS') or []
    if not origins and env == 'development':
        origins = ['http://localhost:5173', 'http://localhost:3000', 'http://127.0.0.1:5173']
    if not origins and env == 'production':
        origins = ['https://melo-frontend.vercel.app']  # Fallback común; mejor configurar CORS_ORIGINS en Render
    CORS(app, origins=origins, supports_credentials=True, allow_headers=['Content-Type', 'Authorization'])

    db.init_app(app)

    # Protección API: validar token en todas las rutas /api/*
    api_secret = app.config.get('API_SECRET') or os.environ.get('API_SECRET') or os.environ.get('AUTH_TOKEN')

    @app.before_request
    def require_auth():
        if not request.path.startswith('/api'):
            return None
        if request.method == 'OPTIONS':
            return None  # CORS preflight no requiere token
        if request.path == '/api/auth/login':
            return None  # Login no requiere token
        if not api_secret:
            return None  # Sin token configurado, no bloquear (solo en dev)
        auth = request.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        token = auth[7:].strip()
        if token != api_secret:
            return jsonify({'error': 'Invalid token'}), 403
        return None

    from app.routes import register_routes
    register_routes(app)

    with app.app_context():
        db.create_all()

    return app
