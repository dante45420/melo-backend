from app.extensions import db


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # plan, web_design, web_maintenance
    price_monthly = db.Column(db.Integer, nullable=False)  # CLP
    deliveries_per_week = db.Column(db.Integer, default=0)  # solo planes
    is_addon = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    client_subscriptions = db.relationship("ClientSubscription", back_populates="subscription")
