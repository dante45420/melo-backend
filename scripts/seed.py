"""Seed inicial: suscripciones, categorías."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import Subscription, ExpenseCategory, IncomeCategory


def seed():
    app = create_app()
    with app.app_context():
        if Subscription.query.first():
            print("Ya existe data, saltando seed.")
            return

        subs = [
            {"name": "Básico", "slug": "basico", "type": "plan", "price_monthly": 39900, "deliveries_per_week": 1, "is_addon": False},
            {"name": "Pro", "slug": "pro", "type": "plan", "price_monthly": 69900, "deliveries_per_week": 1, "is_addon": False},
            {"name": "Full", "slug": "full", "type": "plan", "price_monthly": 119900, "deliveries_per_week": 1, "is_addon": False},
            {"name": "Web diseño", "slug": "web-diseno", "type": "web_design", "price_monthly": 149900, "deliveries_per_week": 0, "is_addon": True},
            {"name": "Web mantención", "slug": "web-mantencion", "type": "web_maintenance", "price_monthly": 29900, "deliveries_per_week": 0, "is_addon": True},
        ]
        for s in subs:
            db.session.add(Subscription(**s))

        ec = ExpenseCategory(name="Marketing", is_marketing=True)
        db.session.add(ec)
        ec2 = ExpenseCategory(name="Operacional", is_marketing=False)
        db.session.add(ec2)

        ic = IncomeCategory(name="Pagos clientes")
        db.session.add(ic)
        ic2 = IncomeCategory(name="Otros ingresos")
        db.session.add(ic2)

        db.session.commit()
        print("Seed completado.")


if __name__ == "__main__":
    seed()
