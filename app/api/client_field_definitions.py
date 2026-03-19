from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models import ClientFieldDefinition

field_defs_bp = Blueprint("client_field_defs", __name__)


@field_defs_bp.route("", methods=["GET"])
def list_definitions():
    items = (
        ClientFieldDefinition.query.order_by(
            ClientFieldDefinition.sort_order,
            ClientFieldDefinition.id,
        ).all()
    )
    return jsonify([_def_to_dict(d) for d in items])


@field_defs_bp.route("", methods=["POST"])
def create_definition():
    data = request.get_json() or {}
    label = (data.get("label") or "").strip()
    if not label:
        return jsonify({"error": "label es obligatorio"}), 400
    sort_order = data.get("sort_order", 0)
    try:
        sort_order = int(sort_order)
    except (TypeError, ValueError):
        sort_order = 0
    d = ClientFieldDefinition(label=label, sort_order=sort_order)
    db.session.add(d)
    db.session.commit()
    return jsonify(_def_to_dict(d)), 201


@field_defs_bp.route("/<int:fid>", methods=["PATCH", "PUT"])
def update_definition(fid):
    d = ClientFieldDefinition.query.get_or_404(fid)
    data = request.get_json() or {}
    if "label" in data:
        label = (data.get("label") or "").strip()
        if not label:
            return jsonify({"error": "label no puede estar vacío"}), 400
        d.label = label
    if "sort_order" in data:
        try:
            d.sort_order = int(data["sort_order"])
        except (TypeError, ValueError):
            return jsonify({"error": "sort_order inválido"}), 400
    db.session.commit()
    return jsonify(_def_to_dict(d))


@field_defs_bp.route("/<int:fid>", methods=["DELETE"])
def delete_definition(fid):
    d = ClientFieldDefinition.query.get_or_404(fid)
    db.session.delete(d)
    db.session.commit()
    return "", 204


def _def_to_dict(d):
    return {"id": d.id, "label": d.label, "sort_order": d.sort_order}
