import os
from functools import wraps
from flask import Blueprint, render_template, redirect, session, send_from_directory

admin_bp = Blueprint("admin", __name__)

STATIC_ADMIN = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "admin")


def _require_admin(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/login")
        return f(*args, **kwargs)
    return inner


@admin_bp.route("/admin")
@admin_bp.route("/admin/<path:path>")
@_require_admin
def serve_admin(path=""):
    if path and os.path.isfile(os.path.join(STATIC_ADMIN, path)):
        return send_from_directory(STATIC_ADMIN, path)
    index_path = os.path.join(STATIC_ADMIN, "index.html")
    if os.path.isfile(index_path):
        return send_from_directory(STATIC_ADMIN, "index.html")
    return render_template("admin.html")
