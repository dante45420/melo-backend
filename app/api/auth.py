from flask import Blueprint, request, jsonify, session

from config import get_admin_credentials

auth_api_bp = Blueprint("auth_api", __name__)


@auth_api_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    user = (data.get("user") or "").strip()
    password = data.get("password") or ""

    try:
        admin_user, admin_password = get_admin_credentials()
    except ValueError:
        return jsonify({"error": "Configuración incompleta"}), 500

    if user == admin_user and password == admin_password:
        session["admin"] = True
        return jsonify({"ok": True})

    return jsonify({"error": "Credenciales incorrectas"}), 401


@auth_api_bp.route("/me", methods=["GET"])
def me():
    if session.get("admin"):
        return jsonify({"ok": True})
    return jsonify({"error": "No autorizado"}), 401


@auth_api_bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("admin", None)
    return jsonify({"ok": True})
