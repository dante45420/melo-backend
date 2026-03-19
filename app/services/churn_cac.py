from datetime import date, timedelta
from sqlalchemy import func

from app.extensions import db
from app.models import ClientSubscription, Subscription, Expense, ExpenseCategory, Payment


def get_churn_for_month(year: int, month: int):
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year, 12, 31)
        next_first = date(year + 1, 1, 1)
    else:
        last_day = date(year, month + 1, 1)
        next_first = last_day

    active_at_start = (
        db.session.query(func.count(func.distinct(ClientSubscription.client_id)))
        .join(Subscription)
        .filter(Subscription.type == "plan")
        .filter(ClientSubscription.status == "active")
        .filter(ClientSubscription.start_date <= first_day)
        .filter(ClientSubscription.end_date >= first_day)
        .scalar()
    ) or 0

    if active_at_start == 0:
        return {"churn_rate": 0, "active_at_start": 0, "churned": 0}

    churned = 0
    subs_ending = (
        ClientSubscription.query
        .join(Subscription)
        .filter(Subscription.type == "plan")
        .filter(ClientSubscription.end_date >= first_day)
        .filter(ClientSubscription.end_date <= last_day)
        .all()
    )
    for cs in subs_ending:
        renewed = Payment.query.filter(
            Payment.client_subscription_id == cs.id,
            Payment.payment_date >= cs.end_date,
            Payment.payment_date < next_first,
        ).first()
        if not renewed:
            churned += 1

    churn_rate = (churned / active_at_start * 100) if active_at_start else 0
    return {
        "churn_rate": round(churn_rate, 2),
        "active_at_start": active_at_start,
        "churned": churned,
    }


def get_cac_for_month(year: int, month: int):
    first_day = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)

    marketing_expenses = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .join(ExpenseCategory)
        .filter(ExpenseCategory.is_marketing == True)
        .filter(Expense.expense_date >= first_day, Expense.expense_date < next_month)
        .scalar()
    ) or 0

    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year, 12, 31)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    subq = (
        db.session.query(ClientSubscription.client_id, func.min(ClientSubscription.start_date).label("first_start"))
        .join(Subscription)
        .filter(Subscription.type == "plan")
        .group_by(ClientSubscription.client_id)
        .subquery()
    )
    new_clients = (
        db.session.query(subq.c.client_id)
        .filter(subq.c.first_start >= first_day)
        .filter(subq.c.first_start <= last_day)
        .count()
    )

    cac = (marketing_expenses / new_clients) if new_clients else 0
    return {
        "cac": int(cac),
        "marketing_expenses": marketing_expenses,
        "new_clients": new_clients,
    }
