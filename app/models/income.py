from app.extensions import db


class IncomeCategory(db.Model):
    __tablename__ = "income_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    incomes = db.relationship("Income", back_populates="category", cascade="all, delete-orphan")


class Income(db.Model):
    __tablename__ = "incomes"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)  # CLP
    income_date = db.Column(db.Date, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("income_categories.id"), nullable=False)
    payment_id = db.Column(db.Integer)  # FK opcional, sin FK para evitar dependencia circular
    source = db.Column(db.String(20), default="manual")  # payment, manual
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    category = db.relationship("IncomeCategory", back_populates="incomes")
