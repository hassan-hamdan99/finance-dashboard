import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "financeiro.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_session():
    """Session manual para scripts e categorizer."""
    return SessionLocal()


def get_db():
    """Dependency generator para FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session():
    """Context manager para uso genérico."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    from models import (
        Category, Transaction, Budget, Investment,
        FinancialTarget, CategoryRule, ImportLog, SubdivisionRule,
    )
    Base.metadata.create_all(engine)
    _seed_categories()


def _seed_categories():
    session = get_session()
    from models import Category

    if session.query(Category).count() == 0:
        defaults = [
            ("Moradia", "#FFCE56", "fixa", "home"),
            ("Mercado", "#FF6384", "variável", "shopping-cart"),
            ("Sair/Comer fora", "#FF9F40", "variável", "utensils"),
            ("Transporte", "#36A2EB", "variável", "car"),
            ("Pets", "#F97316", "variável", "cat"),
            ("Assinaturas", "#8B5CF6", "fixa", "repeat"),
            ("Saúde", "#4BC0C0", "variável", "heart-pulse"),
            ("Educação", "#3B82F6", "variável", "graduation-cap"),
            ("Investimentos", "#00D084", "fixa", "trending-up"),
            ("Salário", "#10B981", "fixa", "banknote"),
            ("Receita", "#22C55E", "fixa", "wallet"),
            ("Faturas", "#F59E0B", "fixa", "credit-card"),
            ("Lazer", "#9966FF", "variável", "gamepad-2"),
            ("Outros", "#94A3B8", "variável", "more-horizontal"),
        ]
        for name, color, tipo, icon in defaults:
            session.add(Category(name=name, color=color, type=tipo, icon=icon))
        session.commit()
    session.close()
