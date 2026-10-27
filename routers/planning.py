from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db
from models import FinancialTarget, Category, Transaction, Investment

router = APIRouter(prefix="/api/planning", tags=["planning"])


class TargetCreate(BaseModel):
    name: str
    category_id: Optional[int] = None
    month: Optional[str] = None  # YYYY-MM
    target_amount: float
    person: Optional[str] = None
    type: str = "expense"  # expense, income, savings
    notes: Optional[str] = None


def _compute_actual(target: FinancialTarget, db: Session, month: str) -> float:
    """Compute the actual amount for a target in a given month."""
    try:
        year, mon = map(int, month.split("-"))
        start = datetime(year, mon, 1).date()
        if mon == 12:
            end = datetime(year + 1, 1, 1).date()
        else:
            end = datetime(year, mon + 1, 1).date()
    except (ValueError, IndexError):
        return 0.0

    if target.type == "expense":
        query = db.query(Transaction).filter(
            Transaction.date >= start,
            Transaction.date < end,
            Transaction.amount < 0,
        )
        if target.category_id:
            query = query.filter(Transaction.category_id == target.category_id)
        if target.person:
            query = query.filter(Transaction.person == target.person)
        total = sum(t.amount for t in query.all())
        return round(abs(total), 2)

    elif target.type == "income":
        query = db.query(Transaction).filter(
            Transaction.date >= start,
            Transaction.date < end,
            Transaction.amount > 0,
        )
        if target.person:
            query = query.filter(Transaction.person == target.person)
        total = sum(t.amount for t in query.all())
        return round(total, 2)

    elif target.type == "savings":
        # Use the latest investment snapshot in the month
        query = db.query(Investment).filter(
            Investment.date >= start,
            Investment.date < end,
        )
        if target.person:
            query = query.filter(Investment.person == target.person)
        total = sum(inv.balance for inv in query.all())
        return round(total, 2)

    return 0.0


@router.get("")
def list_targets(
    month: Optional[str] = None,
    person: Optional[str] = None,
    db: Session = Depends(get_db),
):
    from datetime import date as dt_date
    ref_month = month or dt_date.today().strftime("%Y-%m")

    query = db.query(FinancialTarget)
    # Return targets that are either for the specific month or general (month is null)
    if person:
        query = query.filter(
            (FinancialTarget.person == person) | (FinancialTarget.person.is_(None))
        )

    targets = query.all()
    results = []
    for t in targets:
        cat_name = ""
        if t.category_id:
            cat = db.query(Category).get(t.category_id)
            cat_name = cat.name if cat else ""

        actual = _compute_actual(t, db, ref_month)
        percentage = round((actual / t.target_amount) * 100, 1) if t.target_amount > 0 else 0.0

        results.append({
            "id": t.id,
            "name": t.name,
            "category_name": cat_name,
            "category_id": t.category_id,
            "month": t.month,
            "target_amount": t.target_amount,
            "actual_amount": actual,
            "percentage": percentage,
            "type": t.type,
            "person": t.person,
            "notes": t.notes,
        })

    return results


@router.post("", status_code=201)
def create_target(body: TargetCreate, db: Session = Depends(get_db)):
    if body.category_id:
        cat = db.query(Category).get(body.category_id)
        if not cat:
            raise HTTPException(400, f"Categoria {body.category_id} nao existe")

    target = FinancialTarget(
        name=body.name,
        category_id=body.category_id,
        month=body.month,
        target_amount=body.target_amount,
        person=body.person,
        type=body.type,
        notes=body.notes,
    )
    db.add(target)
    db.commit()
    db.refresh(target)

    cat_name = ""
    if target.category_id:
        cat = db.query(Category).get(target.category_id)
        cat_name = cat.name if cat else ""

    return {
        "id": target.id,
        "name": target.name,
        "category_name": cat_name,
        "category_id": target.category_id,
        "month": target.month,
        "target_amount": target.target_amount,
        "type": target.type,
        "person": target.person,
        "notes": target.notes,
    }


@router.delete("/{target_id}")
def delete_target(target_id: int, db: Session = Depends(get_db)):
    target = db.query(FinancialTarget).get(target_id)
    if not target:
        raise HTTPException(404, "Meta nao encontrada")
    db.delete(target)
    db.commit()
    return {"ok": True, "message": f"Meta '{target.name}' excluida"}


@router.post("/seed", status_code=201)
def seed_targets(db: Session = Depends(get_db)):
    """Seed with example monthly expense targets (demo values)."""
    # Map category names to their target amounts
    seed_data = [
        ("Moradia", 2500.0),
        ("Mercado", 1200.0),
        ("Pets", 300.0),
        ("Assinaturas", 100.0),
        ("Transporte", 400.0),
        ("Sair/Comer fora", 500.0),
        ("Saude", 200.0),
        ("Lazer", 300.0),
    ]

    created = []
    for cat_name, amount in seed_data:
        # Try exact match first, then try "Saude" -> "Saude" (accent-insensitive)
        cat = db.query(Category).filter(Category.name == cat_name).first()
        if not cat:
            # Try with accent: Saude -> Saúde
            cats = db.query(Category).all()
            import unicodedata
            for c in cats:
                norm_name = unicodedata.normalize("NFKD", c.name)
                norm_name = "".join(ch for ch in norm_name if not unicodedata.combining(ch)).lower()
                if norm_name == cat_name.lower():
                    cat = c
                    break

        # Check if target already exists for this category
        existing = None
        if cat:
            existing = db.query(FinancialTarget).filter(
                FinancialTarget.category_id == cat.id,
                FinancialTarget.type == "expense",
                FinancialTarget.person.is_(None),
                FinancialTarget.month.is_(None),
            ).first()

        if existing:
            continue

        target = FinancialTarget(
            name=cat.name if cat else cat_name,
            category_id=cat.id if cat else None,
            month=None,  # general monthly target
            target_amount=amount,
            person=None,  # conjunto
            type="expense",
            notes="Meta mensal de exemplo (seed)",
        )
        db.add(target)
        created.append(target.name)

    db.commit()
    return {"ok": True, "created": created, "message": f"{len(created)} metas criadas"}
