import pandas as pd
from fastapi import APIRouter, Query
from typing import Optional

from analytics.insights import (
    get_transactions_df,
    current_month_kpis,
    category_breakdown,
    monthly_summary,
    generate_insights,
    get_top_expenses,
    category_trends,
    check_budget_alerts,
    detect_recurring_transactions,
    pivot_by_category_month,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _df_to_records(df: pd.DataFrame) -> list:
    """Convert DataFrame to list of dicts with string dates."""
    if df.empty:
        return []
    result = df.copy()
    for col in result.columns:
        if pd.api.types.is_datetime64_any_dtype(result[col]):
            result[col] = result[col].astype(str)
        elif result[col].dtype == "object":
            # Handle datetime.date objects that aren't detected as datetime64
            result[col] = result[col].apply(lambda x: str(x) if hasattr(x, "isoformat") else x)
    return result.to_dict("records")


def _ensure_serializable(data):
    """Ensure all values in a dict/list are JSON serializable."""
    if isinstance(data, dict):
        return {k: _ensure_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_ensure_serializable(item) for item in data]
    elif hasattr(data, "isoformat"):
        return str(data)
    elif isinstance(data, float) and (pd.isna(data) or data != data):
        return 0
    return data


@router.get("/dashboard")
def dashboard(
    months: int = 12,
    person: Optional[str] = None,
    month: Optional[str] = None,
    categories: Optional[str] = None,
):
    df = get_transactions_df(months_back=months, person=person)

    # Filter by categories if provided
    if categories and not df.empty:
        cat_list = [c.strip() for c in categories.split(",") if c.strip()]
        if cat_list:
            df = df[df["category_name"].isin(cat_list)]

    # Determina mês de referência
    from datetime import date as dt_date
    if month:
        ref_month = month
    elif not df.empty:
        latest = df["year_month"].max()
        today_month = dt_date.today().strftime("%Y-%m")
        ref_month = today_month if today_month in df["year_month"].values else latest
    else:
        ref_month = dt_date.today().strftime("%Y-%m")

    kpis = current_month_kpis(df, ref_month=ref_month)
    breakdown = category_breakdown(df, month=ref_month)
    summary = monthly_summary(df)

    return _ensure_serializable({
        "ref_month": ref_month,
        "kpis": kpis,
        "category_breakdown": _df_to_records(breakdown),
        "monthly_summary": _df_to_records(summary),
    })


@router.get("/insights")
def insights(
    person: Optional[str] = None,
    month: Optional[str] = None,
):
    df = get_transactions_df(months_back=12, person=person)
    result = generate_insights(df, ref_month=month)
    return _ensure_serializable(result)


@router.get("/top-expenses")
def top_expenses(
    month: Optional[str] = None,
    person: Optional[str] = None,
    top_n: int = 10,
):
    df = get_transactions_df(months_back=12, person=person)
    top = get_top_expenses(df, month=month, top_n=top_n)
    return _ensure_serializable(_df_to_records(top))


@router.get("/trends")
def trends(
    person: Optional[str] = None,
    month: Optional[str] = None,
):
    df = get_transactions_df(months_back=12, person=person)
    result = category_trends(df, ref_month=month)
    return _ensure_serializable(result)


@router.get("/recurring")
def recurring(
    person: Optional[str] = None,
    months: int = 12,
):
    df = get_transactions_df(months_back=months, person=person)
    result = detect_recurring_transactions(df, months_back=months)
    return _ensure_serializable(result)


@router.get("/pivot")
def pivot(
    months: int = 6,
    person: Optional[str] = None,
):
    df = get_transactions_df(months_back=months, person=person)
    result = pivot_by_category_month(df, months=months)
    return _ensure_serializable(result)


@router.get("/budget-status")
def budget_status(
    month: Optional[str] = None,
    person: Optional[str] = None,
):
    df = get_transactions_df(months_back=12, person=person)
    ref_month = month or pd.Timestamp.now().strftime("%Y-%m")
    alerts = check_budget_alerts(df, ref_month)
    return _ensure_serializable(alerts)
