from datetime import date, timedelta

from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models import Client, ClientSubscription, Payment, Income, IncomeCategory

payments_bp = Blueprint("payments", __name__)


def _parse_date(s):
    if isinstance(s, date):
        return s
    if s:
        return date.fromisoformat(str(s))
    return date.today()


@payments_bp.route("/<int:client_id>/payments", methods=["GET"])
def list_payments(client_id):
    Client.query.get_or_404(client_id)
    payments = Payment.query.filter_by(client_id=client_id).order_by(Payment.payment_date.desc()).all()
    return jsonify([_payment_to_dict(p) for p in payments])


@payments_bp.route("/<int:client_id>/payments", methods=["POST"])
def create_payment(client_id):
    client = Client.query.get_or_404(client_id)
    data = request.get_json()
    amount = data["amount"]
    discount = data.get("discount_applied", 0)
    discount_reason = data.get("discount_reason")
    payment_date = _parse_date(data.get("payment_date"))
    client_subscription_id = data.get("client_subscription_id")
    notes = data.get("notes")

    payment = Payment(
        client_id=client_id,
        client_subscription_id=client_subscription_id,
        amount=amount,
        discount_applied=discount,
        discount_reason=discount_reason,
        payment_date=payment_date,
        notes=notes,
    )
    db.session.add(payment)
    db.session.flush()

    net_amount = amount - discount
    income_cat = IncomeCategory.query.filter_by(name="Pagos clientes").first()
    if not income_cat:
        income_cat = IncomeCategory(name="Pagos clientes")
        db.session.add(income_cat)
        db.session.flush()

    income = Income(
        amount=net_amount,
        income_date=payment_date,
        category_id=income_cat.id,
        payment_id=payment.id,
        source="payment",
        description=f"Pago cliente {client.name}",
    )
    db.session.add(income)

    if client_subscription_id:
        cs = ClientSubscription.query.get(client_subscription_id)
        if cs and cs.client_id == client_id:
            end = _parse_date(cs.end_date)
            cs.end_date = end + timedelta(days=30)
            cs.status = "active"

    db.session.commit()
    return jsonify(_payment_to_dict(payment)), 201


def _payment_to_dict(p):
    return {
        "id": p.id,
        "client_id": p.client_id,
        "client_subscription_id": p.client_subscription_id,
        "amount": p.amount,
        "discount_applied": p.discount_applied,
        "discount_reason": p.discount_reason,
        "payment_date": p.payment_date.isoformat() if p.payment_date else None,
        "notes": p.notes,
    }
