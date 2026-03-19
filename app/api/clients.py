from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models import (
    Client,
    ClientSubscription,
    Subscription,
    ClientFieldDefinition,
    ClientFieldValue,
)

clients_bp = Blueprint("clients", __name__)


@clients_bp.route("", methods=["GET"])
def list_clients():
    clients = Client.query.order_by(Client.name).all()
    return jsonify([_client_to_dict(c) for c in clients])


@clients_bp.route("/<int:client_id>", methods=["GET"])
def get_client(client_id):
    client = Client.query.get_or_404(client_id)
    return jsonify(_client_to_dict(client, include_subscriptions=True))


@clients_bp.route("", methods=["POST"])
def create_client():
    data = request.get_json()
    client = Client(
        name=data["name"],
        email=data.get("email"),
        phone=data.get("phone"),
    )
    db.session.add(client)
    db.session.commit()
    return jsonify(_client_to_dict(client)), 201


@clients_bp.route("/<int:client_id>", methods=["PUT", "PATCH"])
def update_client(client_id):
    client = Client.query.get_or_404(client_id)
    data = request.get_json()
    for key in ("name", "email", "phone", "posts_liked", "posts_disliked", "notes"):
        if key in data:
            setattr(client, key, data[key])
    db.session.commit()
    return jsonify(_client_to_dict(client))


@clients_bp.route("/<int:client_id>/custom-field-values", methods=["GET"])
def get_client_custom_field_values(client_id):
    Client.query.get_or_404(client_id)
    definitions = (
        ClientFieldDefinition.query.order_by(
            ClientFieldDefinition.sort_order,
            ClientFieldDefinition.id,
        ).all()
    )
    rows = ClientFieldValue.query.filter_by(client_id=client_id).all()
    by_def = {r.field_definition_id: r.value for r in rows}
    return jsonify(
        [
            {
                "id": d.id,
                "label": d.label,
                "sort_order": d.sort_order,
                "value": by_def.get(d.id),
            }
            for d in definitions
        ]
    )


@clients_bp.route("/<int:client_id>/custom-field-values", methods=["PUT"])
def put_client_custom_field_values(client_id):
    Client.query.get_or_404(client_id)
    data = request.get_json() or {}
    values = data.get("values")
    if not isinstance(values, dict):
        return jsonify({"error": "values debe ser un objeto { idDefinicion: texto }"}), 400

    for key, text in values.items():
        try:
            def_id = int(key)
        except (TypeError, ValueError):
            return jsonify({"error": f"clave inválida: {key}"}), 400
        if not ClientFieldDefinition.query.get(def_id):
            return jsonify({"error": f"definición {def_id} no existe"}), 404

        row = ClientFieldValue.query.filter_by(
            client_id=client_id,
            field_definition_id=def_id,
        ).first()

        if text is None or (isinstance(text, str) and text.strip() == ""):
            if row:
                db.session.delete(row)
        else:
            val = text if isinstance(text, str) else str(text)
            if row:
                row.value = val
            else:
                db.session.add(
                    ClientFieldValue(
                        client_id=client_id,
                        field_definition_id=def_id,
                        value=val,
                    )
                )

    db.session.commit()
    return get_client_custom_field_values(client_id)


@clients_bp.route("/<int:client_id>/subscriptions", methods=["GET"])
def list_client_subscriptions(client_id):
    client = Client.query.get_or_404(client_id)
    subs = ClientSubscription.query.filter_by(client_id=client_id).order_by(ClientSubscription.start_date.desc()).all()
    return jsonify([_client_sub_to_dict(cs) for cs in subs])


@clients_bp.route("/<int:client_id>/subscriptions", methods=["POST"])
def create_client_subscription(client_id):
    Client.query.get_or_404(client_id)
    data = request.get_json()
    subscription = Subscription.query.get_or_404(data["subscription_id"])
    start_date = data["start_date"]
    end_date = data["end_date"]
    web_enabled = bool(data.get("web_enabled", False))

    if subscription.type != "plan":
        return jsonify({"error": "Solo se pueden asignar planes principales"}), 400

    existing = ClientSubscription.query.join(Subscription).filter(
        ClientSubscription.client_id == client_id,
        Subscription.type == "plan",
        ClientSubscription.status == "active",
    ).first()
    if existing:
        return jsonify({"error": "El cliente ya tiene un plan activo"}), 400

    if web_enabled and not subscription.web_active:
        return jsonify({"error": "Este plan no tiene precios de web configurados"}), 400
    if web_enabled and (
        subscription.web_creation_price is None or subscription.web_maintenance_monthly is None
    ):
        return jsonify({"error": "Completa precios de creación y mantención web en la suscripción"}), 400

    cs = ClientSubscription(
        client_id=client_id,
        subscription_id=subscription.id,
        start_date=start_date,
        end_date=end_date,
        status="active",
        web_enabled=web_enabled,
    )
    db.session.add(cs)
    db.session.commit()
    return jsonify(_client_sub_to_dict(cs)), 201


@clients_bp.route("/<int:client_id>/subscriptions/<int:cs_id>", methods=["PUT", "PATCH"])
def update_client_subscription(client_id, cs_id):
    cs = ClientSubscription.query.filter_by(id=cs_id, client_id=client_id).first_or_404()
    data = request.get_json()
    for key in ("start_date", "end_date", "status", "web_enabled"):
        if key in data:
            if key == "web_enabled":
                val = bool(data[key])
                sub = cs.subscription
                if val and sub and (not sub.web_active or sub.web_creation_price is None or sub.web_maintenance_monthly is None):
                    return jsonify({"error": "Este plan no permite activar web o faltan precios"}), 400
                cs.web_enabled = val
            else:
                setattr(cs, key, data[key])
    db.session.commit()
    return jsonify(_client_sub_to_dict(cs))


@clients_bp.route("/<int:client_id>/subscriptions/<int:cs_id>", methods=["DELETE"])
def cancel_client_subscription(client_id, cs_id):
    cs = ClientSubscription.query.filter_by(id=cs_id, client_id=client_id).first_or_404()
    cs.status = "cancelled"
    db.session.commit()
    return jsonify(_client_sub_to_dict(cs)), 200


def _client_to_dict(client, include_subscriptions=False):
    d = {
        "id": client.id,
        "name": client.name,
        "email": client.email,
        "phone": client.phone,
        "posts_liked": client.posts_liked,
        "posts_disliked": client.posts_disliked,
        "notes": client.notes,
    }
    if include_subscriptions:
        subs = ClientSubscription.query.filter_by(client_id=client.id).all()
        d["subscriptions"] = [_client_sub_to_dict(cs) for cs in subs]
    return d


def _client_sub_to_dict(cs):
    sub = cs.subscription
    return {
        "id": cs.id,
        "subscription_id": cs.subscription_id,
        "subscription_name": sub.name if sub else None,
        "subscription_type": sub.type if sub else None,
        "start_date": cs.start_date.isoformat() if cs.start_date else None,
        "end_date": cs.end_date.isoformat() if cs.end_date else None,
        "status": cs.status,
        "web_enabled": bool(cs.web_enabled) if cs.web_enabled is not None else False,
        "delivery_contents": sub.delivery_contents if sub else None,
        "web_creation_price": sub.web_creation_price if sub else None,
        "web_maintenance_monthly": sub.web_maintenance_monthly if sub else None,
        "plan_web_active": sub.web_active if sub else False,
    }
