"""Rutas de autenticación."""
import os
from flask import Blueprint, request, jsonify

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.route("/login", methods=["POST"])
def login():
    """Valida credenciales admin y devuelve token para las APIs."""
    print("[Melo Auth] POST /login recibido", flush=True)
    data = request.get_json() or {}
    user = (data.get("username") or data.get("user") or "").strip()
    password = (data.get("password") or "").strip()

    admin_user = os.environ.get("ADMIN_USER") or os.environ.get("ADMIN_USERNAME")
    admin_pass = os.environ.get("ADMIN_PASSWORD")

    if not admin_user or not admin_pass:
        return jsonify({"error": "Login no configurado en el servidor"}), 503

    if user != admin_user or password != admin_pass:
        print("[Melo Auth] Credenciales incorrectas", flush=True)
        return jsonify({"error": "Credenciales incorrectas"}), 401

    # Devolver el API_SECRET para que el frontend lo use en las peticiones
    token = os.environ.get("API_SECRET") or os.environ.get("AUTH_TOKEN")
    if not token:
        print("[Melo Auth] API_SECRET no configurado", flush=True)
        return jsonify({"error": "API_SECRET no configurado"}), 503

    print("[Melo Auth] Login OK", flush=True)
    return jsonify({"token": token})
