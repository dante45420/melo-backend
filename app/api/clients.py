from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models import Client, ClientInfo, ClientSubscription, Subscription

clients_bp = Blueprint("clients", __name__)


@clients_bp.route("", methods=["GET"])
def list_clients():
    clients = Client.query.order_by(Client.name).all()
    return jsonify([_client_to_dict(c) for c in clients])


@clients_bp.route("/<int:client_id>", methods=["GET"])
def get_client(client_id):
    client = Client.query.get_or_404(client_id)
    return jsonify(_client_to_dict(client, include_info=True, include_subscriptions=True))


@clients_bp.route("", methods=["POST"])
def create_client():
    data = request.get_json()
    client = Client(
        name=data["name"],
        email=data.get("email"),
        phone=data.get("phone"),
    )
    db.session.add(client)
    db.session.flush()
    info = ClientInfo(client_id=client.id)
    db.session.add(info)
    db.session.commit()
    return jsonify(_client_to_dict(client)), 201


@clients_bp.route("/<int:client_id>", methods=["PUT", "PATCH"])
def update_client(client_id):
    client = Client.query.get_or_404(client_id)
    data = request.get_json()
    for key in ("name", "email", "phone"):
        if key in data:
            setattr(client, key, data[key])
    db.session.commit()
    return jsonify(_client_to_dict(client))


@clients_bp.route("/<int:client_id>/info", methods=["GET"])
def get_client_info(client_id):
    client = Client.query.get_or_404(client_id)
    if not client.client_info:
        info = ClientInfo(client_id=client.id)
        db.session.add(info)
        db.session.commit()
    else:
        info = client.client_info
    return jsonify(_client_info_to_dict(info))


@clients_bp.route("/<int:client_id>/info", methods=["PUT", "PATCH"])
def update_client_info(client_id):
    client = Client.query.get_or_404(client_id)
    if not client.client_info:
        info = ClientInfo(client_id=client.id)
        db.session.add(info)
        db.session.flush()
    else:
        info = client.client_info
    data = request.get_json()
    for key in ("value_proposition_id", "company_info_id", "previous_results_id", "posts_liked", "posts_disliked", "notes"):
        if key in data:
            setattr(info, key, data[key])
    db.session.commit()
    return jsonify(_client_info_to_dict(info))


@clients_bp.route("/<int:client_id>/subscriptions", methods=["GET"])
def list_client_subscriptions(client_id):
    client = Client.query.get_or_404(client_id)
    subs = ClientSubscription.query.filter_by(client_id=client_id).order_by(ClientSubscription.start_date.desc()).all()
    return jsonify([_client_sub_to_dict(cs) for cs in subs])


@clients_bp.route("/<int:client_id>/subscriptions", methods=["POST"])
def create_client_subscription(client_id):
    client = Client.query.get_or_404(client_id)
    data = request.get_json()
    subscription = Subscription.query.get_or_404(data["subscription_id"])
    start_date = data["start_date"]
    end_date = data["end_date"]

    sub_type = subscription.type
    if sub_type == "plan":
        existing = ClientSubscription.query.join(Subscription).filter(
            ClientSubscription.client_id == client_id,
            Subscription.type == "plan",
            ClientSubscription.status == "active",
        ).first()
        if existing:
            return jsonify({"error": "El cliente ya tiene un plan activo"}), 400
    elif sub_type in ("web_design", "web_maintenance"):
        existing = ClientSubscription.query.join(Subscription).filter(
            ClientSubscription.client_id == client_id,
            Subscription.type.in_(("web_design", "web_maintenance")),
            ClientSubscription.status == "active",
        ).first()
        if existing:
            return jsonify({"error": "El cliente ya tiene una suscripción web activa"}), 400

    cs = ClientSubscription(
        client_id=client_id,
        subscription_id=subscription.id,
        start_date=start_date,
        end_date=end_date,
        status="active",
    )
    db.session.add(cs)
    db.session.commit()
    return jsonify(_client_sub_to_dict(cs)), 201


@clients_bp.route("/<int:client_id>/subscriptions/<int:cs_id>", methods=["PUT", "PATCH"])
def update_client_subscription(client_id, cs_id):
    cs = ClientSubscription.query.filter_by(id=cs_id, client_id=client_id).first_or_404()
    data = request.get_json()
    for key in ("start_date", "end_date", "status"):
        if key in data:
            setattr(cs, key, data[key])
    db.session.commit()
    return jsonify(_client_sub_to_dict(cs))


@clients_bp.route("/<int:client_id>/subscriptions/<int:cs_id>", methods=["DELETE"])
def cancel_client_subscription(client_id, cs_id):
    cs = ClientSubscription.query.filter_by(id=cs_id, client_id=client_id).first_or_404()
    cs.status = "cancelled"
    db.session.commit()
    return jsonify(_client_sub_to_dict(cs)), 200


def _client_to_dict(client, include_info=False, include_subscriptions=False):
    d = {"id": client.id, "name": client.name, "email": client.email, "phone": client.phone}
    if include_info and client.client_info:
        d["info"] = _client_info_to_dict(client.client_info)
    if include_subscriptions:
        subs = ClientSubscription.query.filter_by(client_id=client.id).all()
        d["subscriptions"] = [_client_sub_to_dict(cs) for cs in subs]
    return d


def _client_info_to_dict(info):
    d = {
        "id": info.id,
        "value_proposition_id": info.value_proposition_id,
        "company_info_id": info.company_info_id,
        "previous_results_id": info.previous_results_id,
        "posts_liked": info.posts_liked,
        "posts_disliked": info.posts_disliked,
        "notes": info.notes,
    }
    if info.value_proposition:
        d["value_proposition"] = {"id": info.value_proposition.id, "name": info.value_proposition.name, "content": info.value_proposition.content}
    if info.company_info:
        d["company_info"] = {"id": info.company_info.id, "name": info.company_info.name, "content": info.company_info.content}
    if info.previous_results:
        d["previous_results"] = {"id": info.previous_results.id, "name": info.previous_results.name, "content": info.previous_results.content}
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
    }
