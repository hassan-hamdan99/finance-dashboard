from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import date

from database import get_db
from models import Investment

router = APIRouter(prefix="/api/investments", tags=["investments"])


class InvestmentCreate(BaseModel):
    name: str
    type: Optional[str] = None
    balance: float
    date: str  # YYYY-MM-DD
    person: str
    institution: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
def list_investments(
    person: Optional[str] = None,
    db: Session = Depends(get_db),
):
    # Subquery to get the latest date per investment name+person
    latest_sub = (
        db.query(
            Investment.name,
            Investment.person,
            func.max(Investment.date).label("max_date"),
        )
        .group_by(Investment.name, Investment.person)
    )
    if person:
        latest_sub = latest_sub.filter(Investment.person == person)
    latest_sub = latest_sub.subquery()

    # Join to get full records for the latest snapshot
    query = (
        db.query(Investment)
        .join(
            latest_sub,
            (Investment.name == latest_sub.c.name)
            & (Investment.person == latest_sub.c.person)
            & (Investment.date == latest_sub.c.max_date),
        )
        .order_by(Investment.name)
    )

    investments = query.all()

    return [
        {
            "id": inv.id,
            "name": inv.name,
            "type": inv.type,
            "balance": inv.balance,
            "date": str(inv.date),
            "person": inv.person,
            "institution": inv.institution,
            "notes": inv.notes,
        }
        for inv in investments
    ]


@router.get("/history")
def investment_history(
    name: str,
    person: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Investment).filter(Investment.name == name)
    if person:
        query = query.filter(Investment.person == person)

    snapshots = query.order_by(Investment.date.asc()).all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "type": s.type,
            "balance": s.balance,
            "date": str(s.date),
            "person": s.person,
            "institution": s.institution,
            "notes": s.notes,
        }
        for s in snapshots
    ]


@router.post("", status_code=201)
def create_investment(body: InvestmentCreate, db: Session = Depends(get_db)):
    try:
        inv_date = date.fromisoformat(body.date)
    except ValueError:
        raise HTTPException(400, f"Data inválida: {body.date}. Use formato YYYY-MM-DD")

    inv = Investment(
        name=body.name,
        type=body.type,
        balance=body.balance,
        date=inv_date,
        person=body.person,
        institution=body.institution,
        notes=body.notes,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    return {
        "id": inv.id,
        "name": inv.name,
        "type": inv.type,
        "balance": inv.balance,
        "date": str(inv.date),
        "person": inv.person,
        "institution": inv.institution,
        "notes": inv.notes,
    }


@router.delete("/{investment_id}")
def delete_investment(investment_id: int, db: Session = Depends(get_db)):
    inv = db.query(Investment).get(investment_id)
    if not inv:
        raise HTTPException(404, "Investimento não encontrado")

    db.delete(inv)
    db.commit()
    return {"ok": True, "message": f"Investimento '{inv.name}' excluído"}
