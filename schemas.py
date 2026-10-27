from __future__ import annotations

from pydantic import BaseModel, ConfigDict


# ── Category ─────────────────────────────────────────────────────────

class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
    type: str
    icon: str | None = None


class CategoryCreate(BaseModel):
    name: str
    color: str | None = "#94A3B8"
    type: str | None = "variável"
    icon: str | None = None


# ── Transaction ──────────────────────────────────────────────────────

class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: str
    description: str
    amount: float
    category_id: int | None = None
    subcategory: str | None = None
    person: str
    bank: str | None = None
    import_hash: str
    vendor: str | None = None
    payment_method: str | None = None
    subdivision: str = "individual"
    is_recurring: bool = False
    notes: str | None = None
    created_at: str | None = None

    # joined fields
    category_name: str = ""
    category_color: str = "#94A3B8"


class TransactionUpdate(BaseModel):
    category_id: int | None = None
    subcategory: str | None = None
    subdivision: str | None = None
    is_recurring: bool | None = None
    vendor: str | None = None
    payment_method: str | None = None
    notes: str | None = None


class TransactionFilters(BaseModel):
    person: str | None = None
    category_id: int | None = None
    month: str | None = None          # YYYY-MM
    search: str | None = None
    type: str | None = None            # expense / income / all
    date_from: str | None = None
    date_to: str | None = None
    subdivision: str | None = None


# ── Budget ───────────────────────────────────────────────────────────

class BudgetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    category_name: str = ""
    month: str
    limit_amount: float
    person: str | None = None
    spent: float = 0.0


class BudgetCreate(BaseModel):
    category_id: int
    month: str               # YYYY-MM
    limit_amount: float
    person: str | None = None


# ── Investment ───────────────────────────────────────────────────────

class InvestmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str | None = None
    balance: float
    date: str
    person: str
    institution: str | None = None
    notes: str | None = None
    created_at: str | None = None


class InvestmentCreate(BaseModel):
    name: str
    type: str | None = None
    balance: float
    date: str
    person: str
    institution: str | None = None
    notes: str | None = None


# ── FinancialTarget ──────────────────────────────────────────────────

class FinancialTargetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category_id: int | None = None
    category_name: str = ""
    month: str | None = None
    target_amount: float
    person: str | None = None
    type: str = "expense"
    notes: str | None = None


class FinancialTargetCreate(BaseModel):
    name: str
    category_id: int | None = None
    month: str | None = None
    target_amount: float
    person: str | None = None
    type: str = "expense"
    notes: str | None = None


# ── CategoryRule ─────────────────────────────────────────────────────

class CategoryRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keyword: str
    category_id: int
    category_name: str = ""
    priority: int = 5
    source: str = "manual"


class CategoryRuleCreate(BaseModel):
    keyword: str
    category_id: int
    priority: int = 5


# ── Import / Upload ─────────────────────────────────────────────────

class TransactionPreview(BaseModel):
    date: str
    description: str
    amount: float
    category_name: str = ""
    vendor: str | None = None
    payment_method: str | None = None
    is_duplicate: bool = False


class ImportPreviewOut(BaseModel):
    filename: str
    bank: str
    new_count: int
    dup_count: int
    transactions: list[TransactionPreview] = []


# ── Dashboard / Analytics ────────────────────────────────────────────

class KPIsOut(BaseModel):
    total_gastos: float = 0.0
    total_receitas: float = 0.0
    saldo: float = 0.0
    variacao_gastos: float = 0.0
    num_transacoes: float = 0.0
    media_diaria: float = 0.0
    maior_gasto: float = 0.0


class InsightOut(BaseModel):
    text: str
    type: str = "info"       # info / warning / danger / success
    icon: str = ""


class MonthSummaryOut(BaseModel):
    month: str
    gastos: float = 0.0
    receitas: float = 0.0
    saldo: float = 0.0


class CategoryBreakdownOut(BaseModel):
    category: str
    color: str
    total: float = 0.0
    percentage: float = 0.0


class DashboardOut(BaseModel):
    kpis: KPIsOut
    breakdown: list[CategoryBreakdownOut] = []
    monthly_summary: list[MonthSummaryOut] = []
    ref_month: str = ""
