from flask import session, jsonify

from app.api.auth import auth_api_bp
from app.api.subscriptions import subscriptions_bp
from app.api.clients import clients_bp
from app.api.payments import payments_bp
from app.api.deliveries import deliveries_bp
from app.api.accounting import accounting_bp
from app.api.analytics import analytics_bp
from app.api.categories import categories_bp


def register_api_blueprints(flask_app):
    @flask_app.before_request
    def _require_admin_for_api():
        from flask import request
        if request.path.startswith("/api/") and not request.path.startswith("/api/auth/"):
            if not session.get("admin"):
                return jsonify({"error": "No autorizado"}), 401

    flask_app.register_blueprint(auth_api_bp, url_prefix="/api/auth")
    flask_app.register_blueprint(subscriptions_bp, url_prefix="/api/subscriptions")
    flask_app.register_blueprint(clients_bp, url_prefix="/api/clients")
    flask_app.register_blueprint(payments_bp, url_prefix="/api/clients")
    flask_app.register_blueprint(deliveries_bp, url_prefix="/api/deliveries")
    flask_app.register_blueprint(accounting_bp, url_prefix="/api")
    flask_app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    flask_app.register_blueprint(categories_bp, url_prefix="/api")
