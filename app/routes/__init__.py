"""Rutas API."""
from app.routes.auth import bp as auth_bp
from app.routes.clientes import bp as clientes_bp
from app.routes.precios import bp as precios_bp
from app.routes.contabilidad import bp as contabilidad_bp
from app.routes.modelos import bp as modelos_bp


def register_routes(app):
    """Registra todos los blueprints."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(precios_bp)
    app.register_blueprint(contabilidad_bp)
    app.register_blueprint(modelos_bp)
