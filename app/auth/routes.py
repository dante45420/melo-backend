import os
from flask import Blueprint, render_template, request, redirect, session

from config import get_admin_credentials

auth_bp = Blueprint("auth", __name__)


def _frontend_url(path=""):
    base = os.environ.get("FRONTEND_URL", "http://localhost:5173").split(",")[0].strip()
    return f"{base.rstrip('/')}{path}"


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return redirect(_frontend_url("/admin/login"))

    user = request.form.get("user", "").strip()
    password = request.form.get("password", "")

    try:
        admin_user, admin_password = get_admin_credentials()
    except ValueError:
        return render_template("login.html", error="Configuración incompleta"), 500

    if user == admin_user and password == admin_password:
        session["admin"] = True
        return redirect(_frontend_url("/admin"))

    return render_template("login.html", error="Credenciales incorrectas"), 401


@auth_bp.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(_frontend_url("/admin/login"))
