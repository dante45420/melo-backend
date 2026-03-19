from datetime import date, timedelta

from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models import Delivery, Client, ClientSubscription

deliveries_bp = Blueprint("deliveries", __name__)


def _week_start(d):
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return d - timedelta(days=d.weekday())


@deliveries_bp.route("", methods=["GET"])
def list_deliveries():
    client_id = request.args.get("client_id", type=int)
    status = request.args.get("status")
    week_start = request.args.get("week_start")

    q = Delivery.query
    if client_id:
        q = q.filter(Delivery.client_id == client_id)
    if status:
        q = q.filter(Delivery.status == status)
    if week_start:
        ws = date.fromisoformat(week_start)
        ws_end = ws + timedelta(days=6)
        q = q.filter(Delivery.due_date >= ws, Delivery.due_date <= ws_end)
    deliveries = q.order_by(Delivery.due_date.desc()).all()
    return jsonify([_delivery_to_dict(d) for d in deliveries])


@deliveries_bp.route("/<int:delivery_id>", methods=["GET"])
def get_delivery(delivery_id):
    d = Delivery.query.get_or_404(delivery_id)
    return jsonify(_delivery_to_dict(d))


@deliveries_bp.route("", methods=["POST"])
def create_delivery():
    data = request.get_json()
    client_id = data.get("client_id")
    due_date = data["due_date"]
    description = data.get("description")
    type_ = data.get("type", "manual")

    delivery = Delivery(
        client_id=client_id,
        due_date=due_date,
        status="pending",
        type=type_,
        description=description,
    )
    db.session.add(delivery)
    db.session.commit()
    return jsonify(_delivery_to_dict(delivery)), 201


@deliveries_bp.route("/<int:delivery_id>", methods=["PUT", "PATCH"])
def update_delivery(delivery_id):
    d = Delivery.query.get_or_404(delivery_id)
    data = request.get_json()
    for key in ("status", "due_date", "description"):
        if key in data:
            setattr(d, key, data[key])
    db.session.commit()
    return jsonify(_delivery_to_dict(d))


@deliveries_bp.route("/generate", methods=["POST"])
def generate_deliveries():
    data = request.get_json() or {}
    target_week_start = data.get("week_start")
    if target_week_start:
        ws = date.fromisoformat(target_week_start)
    else:
        ws = _week_start(date.today())

    created = 0
    from app.models import Subscription
    active_subs = (
        ClientSubscription.query
        .join(Subscription, ClientSubscription.subscription_id == Subscription.id)
        .filter(ClientSubscription.status == "active")
        .filter(Subscription.deliveries_per_week > 0)
        .all()
    )

    for cs in active_subs:
        sub = cs.subscription
        if sub.deliveries_per_week < 1:
            continue
        existing = Delivery.query.filter_by(
            client_id=cs.client_id,
            due_date=ws,
        ).first()
        if existing:
            continue
        delivery = Delivery(
            client_id=cs.client_id,
            due_date=ws,
            status="pending",
            type="auto",
        )
        db.session.add(delivery)
        created += 1

    db.session.commit()
    return jsonify({"created": created, "week_start": ws.isoformat()})


def _delivery_to_dict(d):
    client_name = None
    if d.client_id:
        c = Client.query.get(d.client_id)
        client_name = c.name if c else None
    return {
        "id": d.id,
        "client_id": d.client_id,
        "client_name": client_name,
        "due_date": d.due_date.isoformat() if d.due_date else None,
        "status": d.status,
        "type": d.type,
        "description": d.description,
    }
