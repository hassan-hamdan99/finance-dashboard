from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db
from models import Budget, Category, Transaction

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


class BudgetCreate(BaseModel):
    category_id: int
    month: str  # YYYY-MM
    limit_amount: float
    person: Optional[str] = None


@router.get("")
def list_budgets(
    month: Optional[str] = None,
    person: Optional[str] = None,
    db: Session = Depends(get_db),
):
    ref_month = month or datetime.now().strftime("%Y-%m")

    query = db.query(Budget).filter(Budget.month == ref_month)
    if person:
        query = query.filter((Budget.person == person) | (Budget.person.is_(None)))

    budgets = query.all()

    # Calculate month date range for spent query
    try:
        year, mon = ref_month.split("-")
        start = datetime(int(year), int(mon), 1).date()
        if int(mon) == 12:
            end = datetime(int(year) + 1, 1, 1).date()
        else:
            end = datetime(int(year), int(mon) + 1, 1).date()
    except (ValueError, IndexError):
        start = end = None

    result = []
    for b in budgets:
        cat = db.query(Category).get(b.category_id)
        cat_name = cat.name if cat else "?"
        cat_color = cat.color if cat else "#94A3B8"

        # Calculate spent amount
        spent = 0.0
        if start and end:
            spent_query = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
                Transaction.category_id == b.category_id,
                Transaction.amount < 0,
                Transaction.date >= start,
                Transaction.date < end,
            )
            if b.person:
                spent_query = spent_query.filter(Transaction.person == b.person)

            spent = abs(float(spent_query.scalar() or 0))

        pct = (spent / b.limit_amount * 100) if b.limit_amount > 0 else 0

        result.append({
            "id": b.id,
            "category_id": b.category_id,
            "category_name": cat_name,
            "category_color": cat_color,
            "month": b.month,
            "limit_amount": b.limit_amount,
            "person": b.person,
            "spent": spent,
            "percentage": round(pct, 1),
        })

    return result


@router.post("", status_code=201)
def create_budget(body: BudgetCreate, db: Session = Depends(get_db)):
    cat = db.query(Category).get(body.category_id)
    if not cat:
        raise HTTPException(400, f"Categoria {body.category_id} não existe")

    existing = db.query(Budget).filter_by(
        category_id=body.category_id,
        month=body.month,
        person=body.person,
    ).first()
    if existing:
        raise HTTPException(400, "Orçamento já existe para esta categoria/mês/pessoa")

    budget = Budget(
        category_id=body.category_id,
        month=body.month,
        limit_amount=body.limit_amount,
        person=body.person,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)

    return {
        "id": budget.id,
        "category_id": budget.category_id,
        "category_name": cat.name,
        "month": budget.month,
        "limit_amount": budget.limit_amount,
        "person": budget.person,
    }


@router.delete("/{budget_id}")
def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    budget = db.query(Budget).get(budget_id)
    if not budget:
        raise HTTPException(404, "Orçamento não encontrado")

    db.delete(budget)
    db.commit()
    return {"ok": True, "message": "Orçamento excluído"}
