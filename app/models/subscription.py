from app.extensions import db


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # plan (único tipo operativo)
    price_monthly = db.Column(db.Integer, nullable=False)  # CLP
    deliveries_per_week = db.Column(db.Integer, default=0)
    # Qué incluye cada “entrega” semanal (posts, reels, carrusel, etc.) — editable en admin
    delivery_contents = db.Column(db.Text)
    # Precios de web asociados a este plan (si web_active)
    web_active = db.Column(db.Boolean, default=False)
    web_creation_price = db.Column(db.Integer)  # único, CLP
    web_maintenance_monthly = db.Column(db.Integer)  # recurrente mensual, CLP
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    client_subscriptions = db.relationship("ClientSubscription", back_populates="subscription")
