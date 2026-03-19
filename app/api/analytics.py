from datetime import date
from sqlalchemy import func

from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models import ClientSubscription, Subscription, Expense, ExpenseCategory, Income, IncomeCategory
from app.services.churn_cac import get_churn_for_month, get_cac_for_month

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/churn", methods=["GET"])
def churn():
    year = request.args.get("year", type=int, default=date.today().year)
    month = request.args.get("month", type=int, default=date.today().month)
    return jsonify(get_churn_for_month(year, month))


@analytics_bp.route("/cac", methods=["GET"])
def cac():
    year = request.args.get("year", type=int, default=date.today().year)
    month = request.args.get("month", type=int, default=date.today().month)
    return jsonify(get_cac_for_month(year, month))


@analytics_bp.route("/dashboard", methods=["GET"])
def dashboard():
    today = date.today()
    year, month = today.year, today.month
    month_str = f"{year:04d}-{month:02d}"

    churn_data = get_churn_for_month(year, month)
    cac_data = get_cac_for_month(year, month)

    marketing_expenses = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .join(ExpenseCategory)
        .filter(ExpenseCategory.is_marketing == True)
        .filter(func.strftime("%Y-%m", Expense.expense_date) == month_str)
        .scalar()
    ) or 0

    total_expenses_month = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(func.strftime("%Y-%m", Expense.expense_date) == month_str)
        .scalar()
    ) or 0

    total_incomes_month = (
        db.session.query(func.coalesce(func.sum(Income.amount), 0))
        .filter(func.strftime("%Y-%m", Income.income_date) == month_str)
        .scalar()
    ) or 0

    total_expenses_all = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).scalar() or 0
    total_incomes_all = db.session.query(func.coalesce(func.sum(Income.amount), 0)).scalar() or 0

    active_clients = (
        db.session.query(func.count(func.distinct(ClientSubscription.client_id)))
        .join(Subscription)
        .filter(Subscription.type == "plan")
        .filter(ClientSubscription.status == "active")
        .filter(ClientSubscription.end_date >= today)
        .scalar()
    ) or 0

    return jsonify({
        "marketing": {
            "cac": cac_data["cac"],
            "cac_new_clients": cac_data["new_clients"],
            "cac_marketing_expenses": cac_data["marketing_expenses"],
            "churn_rate": churn_data["churn_rate"],
            "churn_active_at_start": churn_data["active_at_start"],
            "churn_churned": churn_data["churned"],
        },
        "finanzas": {
            "ingresos_mes": total_incomes_month,
            "gastos_mes": total_expenses_month,
            "balance_mes": total_incomes_month - total_expenses_month,
            "ingresos_acumulado": total_incomes_all,
            "gastos_acumulado": total_expenses_all,
            "balance_acumulado": total_incomes_all - total_expenses_all,
        },
        "active_clients": active_clients,
    })
