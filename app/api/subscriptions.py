from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models import Subscription

subscriptions_bp = Blueprint("subscriptions", __name__)


@subscriptions_bp.route("", methods=["GET"])
def list_subscriptions():
    subs = Subscription.query.order_by(Subscription.type, Subscription.price_monthly).all()
    return jsonify([_sub_to_dict(s) for s in subs])


@subscriptions_bp.route("/<int:sub_id>", methods=["GET"])
def get_subscription(sub_id):
    sub = Subscription.query.get_or_404(sub_id)
    return jsonify(_sub_to_dict(sub))


@subscriptions_bp.route("", methods=["POST"])
def create_subscription():
    data = request.get_json()
    sub = Subscription(
        name=data["name"],
        slug=data["slug"],
        type=data["type"],
        price_monthly=data["price_monthly"],
        deliveries_per_week=data.get("deliveries_per_week", 0),
        is_addon=data.get("is_addon", False),
        description=data.get("description"),
    )
    db.session.add(sub)
    db.session.commit()
    return jsonify(_sub_to_dict(sub)), 201


@subscriptions_bp.route("/<int:sub_id>", methods=["PUT", "PATCH"])
def update_subscription(sub_id):
    sub = Subscription.query.get_or_404(sub_id)
    data = request.get_json()
    for key in ("name", "slug", "type", "price_monthly", "deliveries_per_week", "is_addon", "description"):
        if key in data:
            setattr(sub, key, data[key])
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
        "is_addon": sub.is_addon,
        "description": sub.description,
    }
