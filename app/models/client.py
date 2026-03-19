from app.extensions import db


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    posts_liked = db.Column(db.Text)
    posts_disliked = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    client_subscriptions = db.relationship("ClientSubscription", back_populates="client", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="client", cascade="all, delete-orphan")
    deliveries = db.relationship("Delivery", back_populates="client", cascade="all, delete-orphan")
    custom_field_values = db.relationship(
        "ClientFieldValue",
        back_populates="client",
        cascade="all, delete-orphan",
    )


class ClientSubscription(db.Model):
    __tablename__ = "client_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey("subscriptions.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="active")  # active, cancelled, expired
    web_enabled = db.Column(db.Boolean, default=False)  # cliente con web activa en este plan
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    client = db.relationship("Client", back_populates="client_subscriptions")
    subscription = db.relationship("Subscription", back_populates="client_subscriptions")
    payments = db.relationship("Payment", back_populates="client_subscription", cascade="all, delete-orphan")
