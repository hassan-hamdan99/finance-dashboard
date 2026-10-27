from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import CategoryRule, Category
from categorizer.engine import get_all_rules, add_rule, delete_rule, DEFAULT_RULES

router = APIRouter(prefix="/api/rules", tags=["rules"])


class RuleCreate(BaseModel):
    keyword: str
    category_id: int
    priority: int = 5


@router.get("")
def list_rules(db: Session = Depends(get_db)):
    db_rules = get_all_rules()
    return {
        "rules": db_rules,
        "defaults": DEFAULT_RULES,
    }


@router.post("", status_code=201)
def create_rule(body: RuleCreate, db: Session = Depends(get_db)):
    cat = db.query(Category).get(body.category_id)
    if not cat:
        raise HTTPException(400, f"Categoria {body.category_id} não existe")

    try:
        add_rule(body.keyword, body.category_id, body.priority)
    except Exception as e:
        raise HTTPException(400, str(e))

    return {"ok": True, "message": f"Regra '{body.keyword}' adicionada para '{cat.name}'"}


@router.delete("/{rule_id}")
def remove_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(CategoryRule).get(rule_id)
    if not rule:
        raise HTTPException(404, "Regra não encontrada")

    delete_rule(rule_id)
    return {"ok": True, "message": "Regra excluída"}
