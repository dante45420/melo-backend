from app.extensions import db


class ClientFieldDefinition(db.Model):
    __tablename__ = "client_field_definitions"

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(300), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    values = db.relationship(
        "ClientFieldValue",
        back_populates="definition",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ClientFieldValue(db.Model):
    __tablename__ = "client_field_values"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    field_definition_id = db.Column(
        db.Integer,
        db.ForeignKey("client_field_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    value = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("client_id", "field_definition_id", name="uq_client_field_value_pair"),
    )

    client = db.relationship("Client", back_populates="custom_field_values")
    definition = db.relationship("ClientFieldDefinition", back_populates="values")
