"""Rutas de contabilidad."""
from decimal import Decimal
from flask import Blueprint, request, jsonify
from app.models import RegistroContabilidad, Cliente
from sqlalchemy import func

bp = Blueprint("contabilidad", __name__, url_prefix="/api/contabilidad")


def _registro_json(r):
    return {
        "id": r.id,
        "cliente_id": r.cliente_id,
        "cliente_nombre": r.cliente.nombre if r.cliente else None,
        "instancia_id": r.instancia_id,
        "monto_cobrado": float(r.monto_cobrado),
        "costo_total_generaciones": float(r.costo_total_generaciones),
        "utilidad": float(r.utilidad),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@bp.route("", methods=["GET"])
def listar():
    cliente_id = request.args.get("cliente_id", type=int)
    fecha_desde = request.args.get("fecha_desde")
    fecha_hasta = request.args.get("fecha_hasta")

    q = RegistroContabilidad.query
    if cliente_id:
        q = q.filter_by(cliente_id=cliente_id)
    if fecha_desde:
        q = q.filter(RegistroContabilidad.created_at >= fecha_desde)
    if fecha_hasta:
        q = q.filter(RegistroContabilidad.created_at <= fecha_hasta)
    registros = q.order_by(RegistroContabilidad.created_at.desc()).limit(200).all()
    return jsonify([_registro_json(r) for r in registros])


@bp.route("/resumen", methods=["GET"])
def resumen():
    q = RegistroContabilidad.query
    cliente_id = request.args.get("cliente_id", type=int)
    if cliente_id:
        q = q.filter_by(cliente_id=cliente_id)
    registros = q.all()
    ingresos = sum(r.monto_cobrado for r in registros)
    costos = sum(r.costo_total_generaciones for r in registros)
    utilidad = sum(r.utilidad for r in registros)
    return jsonify({
        "ingresos": float(ingresos),
        "costos": float(costos),
        "utilidad": float(utilidad),
    })
