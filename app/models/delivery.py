from app.extensions import db


class Delivery(db.Model):
    __tablename__ = "deliveries"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"))  # null = pendiente empresa
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending, completed
    type = db.Column(db.String(20), default="auto")  # auto, manual
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    client = db.relationship("Client", back_populates="deliveries")
