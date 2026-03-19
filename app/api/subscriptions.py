from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models import Subscription

subscriptions_bp = Blueprint("subscriptions", __name__)


@subscriptions_bp.route("", methods=["GET"])
def list_subscriptions():
    subs = Subscription.query.order_by(Subscription.price_monthly).all()
    return jsonify([_sub_to_dict(s) for s in subs])


@subscriptions_bp.route("/<int:sub_id>", methods=["GET"])
def get_subscription(sub_id):
    sub = Subscription.query.get_or_404(sub_id)
    return jsonify(_sub_to_dict(sub))


BUNDLED_KEYS = {
    "name",
    "slug",
    "type",
    "price_monthly",
    "deliveries_per_week",
    "delivery_contents",
    "web_active",
    "web_creation_price",
    "web_maintenance_monthly",
    "description",
}


def _opt_int(v):
    if v is None or v == "":
        return None
    return int(v)


@subscriptions_bp.route("", methods=["POST"])
def create_subscription():
    data = request.get_json()
    sub_type = data.get("type", "plan")
    if sub_type != "plan":
        return jsonify({"error": "Solo se permiten suscripciones tipo plan"}), 400
    sub = Subscription(
        name=data["name"],
        slug=data["slug"],
        type="plan",
        price_monthly=int(data["price_monthly"]),
        deliveries_per_week=int(data.get("deliveries_per_week") or 0),
        delivery_contents=data.get("delivery_contents"),
        web_active=bool(data.get("web_active", False)),
        web_creation_price=_opt_int(data.get("web_creation_price")),
        web_maintenance_monthly=_opt_int(data.get("web_maintenance_monthly")),
        description=data.get("description"),
    )
    db.session.add(sub)
    db.session.commit()
    return jsonify(_sub_to_dict(sub)), 201


@subscriptions_bp.route("/<int:sub_id>", methods=["PUT", "PATCH"])
def update_subscription(sub_id):
    sub = Subscription.query.get_or_404(sub_id)
    data = request.get_json()
    if data.get("type") is not None and data["type"] != "plan":
        return jsonify({"error": "Solo se permiten suscripciones tipo plan"}), 400
    for key in BUNDLED_KEYS:
        if key in data:
            val = data[key]
            if key == "web_active":
                val = bool(val)
            elif key in ("web_creation_price", "web_maintenance_monthly"):
                val = _opt_int(val)
            elif key in ("deliveries_per_week", "price_monthly"):
                val = int(val) if val is not None and val != "" else getattr(sub, key)
            setattr(sub, key, val)
    if "type" in data:
        sub.type = "plan"
    db.session.commit()
    return jsonify(_sub_to_dict(sub))


def _sub_to_dict(sub):
    return {
        "id": sub.id,
        "name": sub.name,
        "slug": sub.slug,
        "type": sub.type,
        "price_monthly": sub.price_monthly,
        "deliveries_per_week": sub.deliveries_per_week,
        "delivery_contents": sub.delivery_contents,
        "web_active": sub.web_active,
        "web_creation_price": sub.web_creation_price,
        "web_maintenance_monthly": sub.web_maintenance_monthly,
        "description": sub.description,
    }
