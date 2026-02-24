"""Rutas de precios."""
from decimal import Decimal
from flask import Blueprint, request, jsonify
from app import db
from app.models import PrecioTarifa

bp = Blueprint("precios", __name__, url_prefix="/api/precios")


@bp.route("", methods=["GET"])
def obtener():
    tarifas = PrecioTarifa.query.all()
    out = {}
    for t in tarifas:
        out[t.tipo] = float(t.precio)
    # Valores por defecto si no existen
    for tipo in ["imagen", "carrusel", "video"]:
        if tipo not in out:
            out[tipo] = 0
    return jsonify(out)


@bp.route("", methods=["PUT"])
def actualizar():
    data = request.get_json() or {}
    for tipo, precio in data.items():
        if tipo not in ("imagen", "carrusel", "video"):
            continue
        t = PrecioTarifa.query.filter_by(tipo=tipo).first()
        precio_val = Decimal(str(precio))
        if t:
            t.precio = precio_val
        else:
            t = PrecioTarifa(tipo=tipo, precio=precio_val)
            db.session.add(t)
    db.session.commit()
    tarifas = PrecioTarifa.query.all()
    out = {t.tipo: float(t.precio) for t in tarifas}
    for tipo in ("imagen", "carrusel", "video"):
        out.setdefault(tipo, 0)
    return jsonify(out)
