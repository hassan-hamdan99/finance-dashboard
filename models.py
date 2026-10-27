from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Boolean,
    ForeignKey, UniqueConstraint, func,
)
from sqlalchemy.orm import relationship
from database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(20), default="#94A3B8")
    type = Column(String(20), default="variável")  # fixa / variável
    icon = Column(String(50), nullable=True)

    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category")
    rules = relationship("CategoryRule", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    description = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)  # negativo = gasto, positivo = receita
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    subcategory = Column(String(100), nullable=True)  # texto livre: "Minerva", "Uber"
    person = Column(String(100), nullable=False)
    bank = Column(String(100), nullable=True)
    import_hash = Column(String(64), unique=True, nullable=False)
    vendor = Column(String(200), nullable=True)  # provedor: Petlove, Angeloni
    payment_method = Column(String(50), nullable=True)  # credito_vista, credito_parcelado, pix, boleto, debito
    subdivision = Column(String(20), default="individual")  # individual / conjunto
    is_recurring = Column(Boolean, default=False)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    category = relationship("Category", back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    month = Column(String(7), nullable=False)  # "2026-03"
    limit_amount = Column(Float, nullable=False)
    person = Column(String(100), nullable=True)  # None = ambos

    category = relationship("Category", back_populates="budgets")

    __table_args__ = (
        UniqueConstraint("category_id", "month", "person", name="uq_budget"),
    )


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)  # "Caixinha Turbo Ultravioleta"
    type = Column(String(50), nullable=True)  # renda_fixa, caixinha, crypto, poupanca
    balance = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    person = Column(String(100), nullable=False)
    institution = Column(String(100), nullable=True)  # Nubank, XP
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class FinancialTarget(Base):
    __tablename__ = "financial_targets"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)  # "Previdência", "Apartamento"
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    month = Column(String(7), nullable=True)  # YYYY-MM, null = meta geral
    target_amount = Column(Float, nullable=False)
    person = Column(String(100), nullable=True)  # None = ambos
    type = Column(String(20), default="expense")  # expense, income, savings
    notes = Column(String(500), nullable=True)


class CategoryRule(Base):
    __tablename__ = "category_rules"

    id = Column(Integer, primary_key=True)
    keyword = Column(String(200), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    priority = Column(Integer, default=5)
    source = Column(String(20), default="manual")  # manual / learned

    category = relationship("Category", back_populates="rules")

    __table_args__ = (
        UniqueConstraint("keyword", "category_id", name="uq_rule"),
    )


class SubdivisionRule(Base):
    __tablename__ = "subdivision_rules"

    id = Column(Integer, primary_key=True)
    keyword = Column(String(200), nullable=False)  # normalized vendor/description keyword
    person = Column(String(100), nullable=False)
    subdivision = Column(String(20), nullable=False)  # individual / conjunto

    __table_args__ = (
        UniqueConstraint("keyword", "person", name="uq_subdivision_rule"),
    )


class ImportLog(Base):
    __tablename__ = "import_logs"

    id = Column(Integer, primary_key=True)
    filename = Column(String(500), nullable=False)
    imported_at = Column(DateTime, server_default=func.now())
    record_count = Column(Integer, default=0)
    bank = Column(String(100), nullable=True)
    person = Column(String(100), nullable=True)
