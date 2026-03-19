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
            {
                "name": "Básico",
                "slug": "basico",
                "type": "plan",
                "price_monthly": 39900,
                "deliveries_per_week": 1,
                "delivery_contents": "2 posts + 3 historias/semana · 1 entrega semanal",
                "web_active": True,
                "web_creation_price": 149900,
                "web_maintenance_monthly": 29900,
            },
            {
                "name": "Pro",
                "slug": "pro",
                "type": "plan",
                "price_monthly": 69900,
                "deliveries_per_week": 1,
                "delivery_contents": "4 posts (1 reel) + 7 historias/semana · 1 entrega semanal",
                "web_active": True,
                "web_creation_price": 119900,
                "web_maintenance_monthly": 24900,
            },
            {
                "name": "Full",
                "slug": "full",
                "type": "plan",
                "price_monthly": 119900,
                "deliveries_per_week": 1,
                "delivery_contents": "5 posts (2 reels) + 14 historias/semana · 1 entrega semanal",
                "web_active": True,
                "web_creation_price": 89900,
                "web_maintenance_monthly": 19900,
            },
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
