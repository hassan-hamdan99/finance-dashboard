from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db
from models import Transaction, Category
from categorizer.engine import learn_from_override, learn_subdivision

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


class TransactionUpdate(BaseModel):
    category_id: Optional[int] = None
    subcategory: Optional[str] = None
    subdivision: Optional[str] = None
    is_recurring: Optional[bool] = None
    vendor: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None


def _apply_filters(query, db, person, category_id, month, search, type_, date_from, date_to, subdivision):
    """Apply common filters to a transaction query."""
    if person:
        query = query.filter(Transaction.person == person)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if month:
        # month format: YYYY-MM
        try:
            year, mon = month.split("-")
            start = datetime(int(year), int(mon), 1).date()
            if int(mon) == 12:
                end = datetime(int(year) + 1, 1, 1).date()
            else:
                end = datetime(int(year), int(mon) + 1, 1).date()
            query = query.filter(Transaction.date >= start, Transaction.date < end)
        except (ValueError, IndexError):
            pass
    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))
    if type_ == "expense":
        query = query.filter(Transaction.amount < 0)
    elif type_ == "income":
        query = query.filter(Transaction.amount > 0)
    if date_from:
        try:
            query = query.filter(Transaction.date >= datetime.strptime(date_from, "%Y-%m-%d").date())
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(Transaction.date <= datetime.strptime(date_to, "%Y-%m-%d").date())
        except ValueError:
            pass
    if subdivision:
        query = query.filter(Transaction.subdivision == subdivision)
    return query


def _serialize_transaction(t, category_name):
    return {
        "id": t.id,
        "date": str(t.date),
        "description": t.description,
        "amount": t.amount,
        "category_id": t.category_id,
        "category_name": category_name,
        "subcategory": t.subcategory,
        "person": t.person,
        "bank": t.bank,
        "vendor": t.vendor,
        "payment_method": t.payment_method,
        "subdivision": t.subdivision,
        "is_recurring": t.is_recurring,
        "notes": t.notes,
    }


@router.get("")
def list_transactions(
    person: Optional[str] = None,
    category_id: Optional[int] = None,
    month: Optional[str] = None,
    search: Optional[str] = None,
    type: Optional[str] = Query(None, alias="type"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    subdivision: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    db: Session = Depends(get_db),
):
    query = (
        db.query(Transaction, Category.name.label("category_name"))
        .outerjoin(Category, Transaction.category_id == Category.id)
    )
    query = _apply_filters(query, db, person, category_id, month, search, type, date_from, date_to, subdivision)

    total = query.count()
    rows = (
        query.order_by(Transaction.date.desc(), Transaction.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    items = [_serialize_transaction(t, cat_name) for t, cat_name in rows]

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
    }


@router.get("/summary")
def transactions_summary(
    person: Optional[str] = None,
    category_id: Optional[int] = None,
    month: Optional[str] = None,
    search: Optional[str] = None,
    type: Optional[str] = Query(None, alias="type"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    subdivision: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Transaction)
    query = _apply_filters(query, db, person, category_id, month, search, type, date_from, date_to, subdivision)

    rows = query.all()
    total_gastos = sum(t.amount for t in rows if t.amount < 0)
    total_receitas = sum(t.amount for t in rows if t.amount > 0)

    return {
        "total_gastos": abs(total_gastos),
        "total_receitas": total_receitas,
        "count": len(rows),
    }


@router.get("/persons")
def list_persons(db: Session = Depends(get_db)):
    results = db.query(Transaction.person).distinct().all()
    persons = sorted(set(p[0] for p in results if p[0]))
    return persons


@router.patch("/{transaction_id}")
def update_transaction(transaction_id: int, body: TransactionUpdate, db: Session = Depends(get_db)):
    txn = db.query(Transaction).get(transaction_id)
    if not txn:
        raise HTTPException(404, "Transação não encontrada")

    old_category_id = txn.category_id

    if body.category_id is not None:
        cat = db.query(Category).get(body.category_id)
        if not cat:
            raise HTTPException(400, f"Categoria {body.category_id} não existe")
        txn.category_id = body.category_id
    if body.subcategory is not None:
        txn.subcategory = body.subcategory
    if body.subdivision is not None:
        txn.subdivision = body.subdivision
    if body.is_recurring is not None:
        txn.is_recurring = body.is_recurring
    if body.vendor is not None:
        txn.vendor = body.vendor
    if body.payment_method is not None:
        txn.payment_method = body.payment_method
    if body.notes is not None:
        txn.notes = body.notes

    db.commit()
    db.refresh(txn)

    # Learn from category override
    if body.category_id is not None and body.category_id != old_category_id:
        try:
            learn_from_override(txn.description, body.category_id)
        except Exception:
            pass  # don't fail the update if learning fails

    # Learn from subdivision override
    if body.subdivision is not None:
        try:
            learn_subdivision(txn.description, txn.person, body.subdivision)
        except Exception:
            pass  # don't fail the update if learning fails

    cat_name = None
    if txn.category_id:
        cat = db.query(Category).get(txn.category_id)
        cat_name = cat.name if cat else None

    return _serialize_transaction(txn, cat_name)


@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    txn = db.query(Transaction).get(transaction_id)
    if not txn:
        raise HTTPException(404, "Transação não encontrada")

    db.delete(txn)
    db.commit()
    return {"ok": True, "message": "Transação excluída"}
