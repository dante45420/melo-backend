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

    @app.after_request
    def add_cors_to_all(resp):
        """Garantiza CORS en todas las respuestas (incl. 500/503) para que el frontend reciba el error."""
        origin = request.headers.get('Origin')
        if not origin:
            return resp
        # Permitir si el origen está en la lista o es el frontend de Vercel (fallback en Render)
        norm = origin.rstrip('/')
        allowed = (origins and norm in [o.rstrip('/') for o in origins]) or 'melo-frontend.vercel.app' in origin
        if allowed:
            resp.headers['Access-Control-Allow-Origin'] = origin
            resp.headers['Access-Control-Allow-Credentials'] = 'true'
            resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return resp

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
        # Migración: añadir motivo_rechazo si no existe (para deploys sin ejecutar migrate manualmente)
        try:
            from sqlalchemy import text, inspect
            insp = inspect(db.engine)
            cols = [c["name"] for c in insp.get_columns("generaciones")]
            if "motivo_rechazo" not in cols:
                db.session.execute(text("ALTER TABLE generaciones ADD COLUMN motivo_rechazo TEXT"))
                db.session.commit()
                _log("Columna motivo_rechazo añadida.")
            if "fal_request_id" not in cols:
                db.session.execute(text("ALTER TABLE generaciones ADD COLUMN fal_request_id VARCHAR(100)"))
                db.session.execute(text("ALTER TABLE generaciones ADD COLUMN fal_model VARCHAR(200)"))
                db.session.commit()
                _log("Columnas fal_request_id, fal_model añadidas.")
        except Exception as e:
            _log(f"Migración: {e}")

    return app
