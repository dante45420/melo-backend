"""Factory de la aplicación Flask."""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _log(msg):
    print(f"[Melo] {msg}", flush=True)


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

    # CORS: orígenes de CORS_ORIGINS (ej: https://melo-frontend.vercel.app)
    origins = app.config.get('CORS_ORIGINS') or []
    CORS(
        app,
        origins=origins,
        supports_credentials=True,
        allow_headers=['Content-Type', 'Authorization'],
        methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        expose_headers=['Authorization'],
        intercept_exceptions=True,
    )

    @app.errorhandler(500)
    def handle_500(e):
        """Devuelve JSON con CORS para que el frontend reciba el error."""
        import traceback
        _log(f"500 error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor"}), 500

    db.init_app(app)

    # Protección API: validar token en todas las rutas /api/*
    api_secret = app.config.get('API_SECRET') or os.environ.get('API_SECRET') or os.environ.get('AUTH_TOKEN')

    @app.before_request
    def log_and_handle_options():
        _log(f"{request.method} {request.path}")
        # OPTIONS debe responder 204 aquí para CORS preflight (antes del routing)
        if request.method == 'OPTIONS':
            resp = app.make_response(('', 204))
            return resp
        return None

    @app.before_request
    def require_auth():
        if not request.path.startswith('/api'):
            return None
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
