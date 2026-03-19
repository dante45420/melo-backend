from app.extensions import db


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    client_subscription_id = db.Column(db.Integer, db.ForeignKey("client_subscriptions.id"))
    amount = db.Column(db.Integer, nullable=False)  # CLP
    discount_applied = db.Column(db.Integer, default=0)
    discount_reason = db.Column(db.String(200))
    payment_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    client = db.relationship("Client", back_populates="payments")
    client_subscription = db.relationship("ClientSubscription", back_populates="payments")
