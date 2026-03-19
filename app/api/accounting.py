from flask import Blueprint, request, jsonify

from sqlalchemy import func
from app.extensions import db
from app.models import Expense, ExpenseCategory, Income, IncomeCategory

accounting_bp = Blueprint("accounting", __name__)


@accounting_bp.route("/expenses", methods=["GET"])
def list_expenses():
    category_id = request.args.get("category_id", type=int)
    month = request.args.get("month")
    q = Expense.query
    if category_id:
        q = q.filter(Expense.category_id == category_id)
    if month:
        q = q.filter(func.strftime("%Y-%m", Expense.expense_date) == month)
    expenses = q.order_by(Expense.expense_date.desc()).all()
    return jsonify([_expense_to_dict(e) for e in expenses])


@accounting_bp.route("/expenses", methods=["POST"])
def create_expense():
    data = request.get_json()
    expense = Expense(
        amount=data["amount"],
        expense_date=data["expense_date"],
        category_id=data["category_id"],
        description=data.get("description"),
    )
    db.session.add(expense)
    db.session.commit()
    return jsonify(_expense_to_dict(expense)), 201


@accounting_bp.route("/expenses/<int:expense_id>", methods=["PUT", "PATCH"])
def update_expense(expense_id):
    e = Expense.query.get_or_404(expense_id)
    data = request.get_json()
    for key in ("amount", "expense_date", "category_id", "description"):
        if key in data:
            setattr(e, key, data[key])
    db.session.commit()
    return jsonify(_expense_to_dict(e))


@accounting_bp.route("/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    e = Expense.query.get_or_404(expense_id)
    db.session.delete(e)
    db.session.commit()
    return "", 204


@accounting_bp.route("/expense-categories", methods=["GET"])
def list_expense_categories():
    cats = ExpenseCategory.query.order_by(ExpenseCategory.name).all()
    return jsonify([_expense_cat_to_dict(c) for c in cats])


@accounting_bp.route("/expense-categories", methods=["POST"])
def create_expense_category():
    data = request.get_json()
    cat = ExpenseCategory(
        name=data["name"],
        is_marketing=data.get("is_marketing", False),
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify(_expense_cat_to_dict(cat)), 201


@accounting_bp.route("/expense-categories/<int:cat_id>", methods=["PUT", "PATCH"])
def update_expense_category(cat_id):
    c = ExpenseCategory.query.get_or_404(cat_id)
    data = request.get_json()
    for key in ("name", "is_marketing"):
        if key in data:
            setattr(c, key, data[key])
    db.session.commit()
    return jsonify(_expense_cat_to_dict(c))


@accounting_bp.route("/expense-categories/<int:cat_id>", methods=["DELETE"])
def delete_expense_category(cat_id):
    c = ExpenseCategory.query.get_or_404(cat_id)
    db.session.delete(c)
    db.session.commit()
    return "", 204


@accounting_bp.route("/incomes", methods=["GET"])
def list_incomes():
    category_id = request.args.get("category_id", type=int)
    month = request.args.get("month")
    q = Income.query
    if category_id:
        q = q.filter(Income.category_id == category_id)
    if month:
        q = q.filter(func.strftime("%Y-%m", Income.income_date) == month)
    incomes = q.order_by(Income.income_date.desc()).all()
    return jsonify([_income_to_dict(i) for i in incomes])


@accounting_bp.route("/income-categories", methods=["GET"])
def list_income_categories():
    cats = IncomeCategory.query.order_by(IncomeCategory.name).all()
    return jsonify([_income_cat_to_dict(c) for c in cats])


@accounting_bp.route("/income-categories", methods=["POST"])
def create_income_category():
    data = request.get_json()
    cat = IncomeCategory(name=data["name"])
    db.session.add(cat)
    db.session.commit()
    return jsonify(_income_cat_to_dict(cat)), 201


@accounting_bp.route("/income-categories/<int:cat_id>", methods=["PUT", "PATCH"])
def update_income_category(cat_id):
    c = IncomeCategory.query.get_or_404(cat_id)
    data = request.get_json()
    if "name" in data:
        c.name = data["name"]
    db.session.commit()
    return jsonify(_income_cat_to_dict(c))


@accounting_bp.route("/income-categories/<int:cat_id>", methods=["DELETE"])
def delete_income_category(cat_id):
    c = IncomeCategory.query.get_or_404(cat_id)
    db.session.delete(c)
    db.session.commit()
    return "", 204


@accounting_bp.route("/incomes", methods=["POST"])
def create_income():
    data = request.get_json()
    income = Income(
        amount=data["amount"],
        income_date=data["income_date"],
        category_id=data["category_id"],
        source="manual",
        description=data.get("description"),
    )
    db.session.add(income)
    db.session.commit()
    return jsonify(_income_to_dict(income)), 201


def _expense_to_dict(e):
    return {
        "id": e.id,
        "amount": e.amount,
        "expense_date": e.expense_date.isoformat() if e.expense_date else None,
        "category_id": e.category_id,
        "category_name": e.category.name if e.category else None,
        "description": e.description,
    }


def _expense_cat_to_dict(c):
    return {"id": c.id, "name": c.name, "is_marketing": c.is_marketing}


def _income_cat_to_dict(c):
    return {"id": c.id, "name": c.name}


def _income_to_dict(i):
    return {
        "id": i.id,
        "amount": i.amount,
        "income_date": i.income_date.isoformat() if i.income_date else None,
        "category_id": i.category_id,
        "category_name": i.category.name if i.category else None,
        "payment_id": i.payment_id,
        "source": i.source,
        "description": i.description,
    }
