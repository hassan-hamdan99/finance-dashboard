from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models import Category

router = APIRouter(prefix="/api/categories", tags=["categories"])


class CategoryCreate(BaseModel):
    name: str
    color: str = "#94A3B8"
    type: str = "variável"
    icon: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    type: Optional[str] = None
    icon: Optional[str] = None


@router.get("")
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(Category).order_by(Category.name).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "color": c.color,
            "type": c.type,
            "icon": c.icon,
        }
        for c in cats
    ]


@router.post("", status_code=201)
def create_category(body: CategoryCreate, db: Session = Depends(get_db)):
    existing = db.query(Category).filter_by(name=body.name).first()
    if existing:
        raise HTTPException(400, f"Categoria '{body.name}' já existe")

    cat = Category(name=body.name, color=body.color, type=body.type, icon=body.icon)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return {"id": cat.id, "name": cat.name, "color": cat.color, "type": cat.type, "icon": cat.icon}


@router.patch("/{category_id}")
def update_category(category_id: int, body: CategoryUpdate, db: Session = Depends(get_db)):
    cat = db.query(Category).get(category_id)
    if not cat:
        raise HTTPException(404, "Categoria não encontrada")

    if body.name is not None:
        dup = db.query(Category).filter(Category.name == body.name, Category.id != category_id).first()
        if dup:
            raise HTTPException(400, f"Categoria '{body.name}' já existe")
        cat.name = body.name
    if body.color is not None:
        cat.color = body.color
    if body.type is not None:
        cat.type = body.type
    if body.icon is not None:
        cat.icon = body.icon

    db.commit()
    db.refresh(cat)
    return {"id": cat.id, "name": cat.name, "color": cat.color, "type": cat.type, "icon": cat.icon}


@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(Category).get(category_id)
    if not cat:
        raise HTTPException(404, "Categoria não encontrada")

    if cat.transactions:
        raise HTTPException(
            400,
            f"Não é possível excluir: {len(cat.transactions)} transação(ões) vinculada(s)",
        )

    db.delete(cat)
    db.commit()
    return {"ok": True, "message": f"Categoria '{cat.name}' excluída"}
