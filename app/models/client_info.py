from app.extensions import db


class ValueProposition(db.Model):
    __tablename__ = "value_propositions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class CompanyInfo(db.Model):
    __tablename__ = "company_infos"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class PreviousResults(db.Model):
    __tablename__ = "previous_results"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class ClientInfo(db.Model):
    __tablename__ = "client_infos"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False, unique=True)
    value_proposition_id = db.Column(db.Integer, db.ForeignKey("value_propositions.id"))
    company_info_id = db.Column(db.Integer, db.ForeignKey("company_infos.id"))
    previous_results_id = db.Column(db.Integer, db.ForeignKey("previous_results.id"))
    posts_liked = db.Column(db.Text)  # JSON array o texto libre
    posts_disliked = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    client = db.relationship("Client", back_populates="client_info")
    value_proposition = db.relationship("ValueProposition")
    company_info = db.relationship("CompanyInfo")
    previous_results = db.relationship("PreviousResults")
