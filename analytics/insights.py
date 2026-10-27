import pandas as pd
from datetime import date, timedelta
from database import get_session
from models import Transaction, Category, Budget
from sqlalchemy import func, extract


def get_transactions_df(months_back: int = 12, person: str = None) -> pd.DataFrame:
    """Carrega transações como DataFrame."""
    session = get_session()
    query = session.query(
        Transaction.id,
        Transaction.date,
        Transaction.description,
        Transaction.amount,
        Transaction.person,
        Transaction.bank,
        Transaction.category_id,
        Transaction.subcategory,
        Transaction.vendor,
        Transaction.payment_method,
        Transaction.subdivision,
        Transaction.is_recurring,
        Category.name.label("category_name"),
        Category.color.label("category_color"),
    ).outerjoin(Category)

    if months_back:
        start_date = date.today() - timedelta(days=months_back * 30)
        query = query.filter(Transaction.date >= start_date)

    if person and person != "Todos":
        query = query.filter(Transaction.person == person)

    rows = query.all()
    session.close()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=[
        "id", "date", "description", "amount", "person", "bank",
        "category_id", "subcategory", "vendor", "payment_method",
        "subdivision", "is_recurring", "category_name", "category_color",
    ])
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    return df


def get_persons():
    """Lista de pessoas cadastradas."""
    session = get_session()
    persons = session.query(Transaction.person).distinct().all()
    session.close()
    return sorted(set(p[0] for p in persons if p[0]))


def get_categories():
    """Lista de categorias com cores."""
    session = get_session()
    cats = session.query(Category).all()
    session.close()
    return {c.id: {"name": c.name, "color": c.color} for c in cats}


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Resumo mensal de gastos e receitas."""
    if df.empty:
        return pd.DataFrame()

    expenses = df[df["amount"] < 0].copy()
    income = df[df["amount"] > 0].copy()

    exp_monthly = expenses.groupby("year_month")["amount"].sum().abs().reset_index()
    exp_monthly.columns = ["month", "gastos"]

    inc_monthly = income.groupby("year_month")["amount"].sum().reset_index()
    inc_monthly.columns = ["month", "receitas"]

    summary = pd.merge(exp_monthly, inc_monthly, on="month", how="outer").fillna(0)
    summary["saldo"] = summary["receitas"] - summary["gastos"]
    summary = summary.sort_values("month")
    return summary


def category_breakdown(df: pd.DataFrame, month: str = None) -> pd.DataFrame:
    """Gastos por categoria."""
    if df.empty:
        return pd.DataFrame()

    expenses = df[df["amount"] < 0].copy()
    if month:
        expenses = expenses[expenses["year_month"] == month]

    if expenses.empty:
        return pd.DataFrame()

    breakdown = (
        expenses.groupby(["category_name", "category_color"])["amount"]
        .sum()
        .abs()
        .reset_index()
    )
    breakdown.columns = ["category", "color", "total"]
    breakdown = breakdown.sort_values("total", ascending=False)
    return breakdown


def current_month_kpis(df: pd.DataFrame, ref_month: str = None) -> dict:
    """KPIs do mês de referência (default: mês atual)."""
    import calendar
    today = date.today()
    current_month = ref_month or today.strftime("%Y-%m")

    # Calcula mês anterior ao mês de referência
    ref_year, ref_mon = map(int, current_month.split("-"))
    if ref_mon == 1:
        prev_month = f"{ref_year - 1}-12"
    else:
        prev_month = f"{ref_year}-{ref_mon - 1:02d}"

    result = {
        "total_gastos": 0,
        "total_receitas": 0,
        "media_diaria": 0,
        "num_transacoes": 0,
        "variacao_gastos": 0,
        "projecao_mensal": 0,
        "saldo": 0,
    }

    if df.empty:
        return result

    current = df[df["year_month"] == current_month]
    previous = df[df["year_month"] == prev_month]

    gastos_atual = current[current["amount"] < 0]["amount"].sum()
    receitas_atual = current[current["amount"] > 0]["amount"].sum()
    gastos_anterior = previous[previous["amount"] < 0]["amount"].sum()

    result["total_gastos"] = abs(gastos_atual)
    result["total_receitas"] = receitas_atual
    result["saldo"] = receitas_atual + gastos_atual
    result["num_transacoes"] = len(current)

    # Dias no mês de referência
    dias_no_mes = calendar.monthrange(ref_year, ref_mon)[1]

    # Se é o mês atual, usa dias passados; se é mês anterior, usa dias totais
    if current_month == today.strftime("%Y-%m"):
        dias_passados = today.day
    else:
        dias_passados = dias_no_mes  # mês completo

    if dias_passados > 0:
        result["media_diaria"] = abs(gastos_atual) / dias_passados
        result["projecao_mensal"] = result["media_diaria"] * dias_no_mes

    if gastos_anterior != 0:
        result["variacao_gastos"] = (
            (abs(gastos_atual) - abs(gastos_anterior)) / abs(gastos_anterior)
        ) * 100

    return result


def get_top_expenses(df: pd.DataFrame, month: str = None, top_n: int = 10) -> pd.DataFrame:
    """Maiores gastos."""
    if df.empty:
        return pd.DataFrame()

    expenses = df[df["amount"] < 0].copy()
    if month:
        expenses = expenses[expenses["year_month"] == month]

    expenses["abs_amount"] = expenses["amount"].abs()
    top = expenses.nlargest(top_n, "abs_amount")
    return top[["date", "description", "abs_amount", "category_name", "person"]].reset_index(drop=True)


def detect_anomalies(df: pd.DataFrame, ref_month: str = None) -> list:
    """Detecta gastos anômalos (>2x a média da categoria)."""
    if df.empty:
        return []

    current_month = ref_month or date.today().strftime("%Y-%m")
    expenses = df[df["amount"] < 0].copy()

    anomalies = []
    for cat in expenses["category_name"].unique():
        cat_data = expenses[expenses["category_name"] == cat]
        cat_current = cat_data[cat_data["year_month"] == current_month]

        if len(cat_data) < 5 or cat_current.empty:
            continue

        mean = cat_data["amount"].abs().mean()
        std = cat_data["amount"].abs().std()

        for _, row in cat_current.iterrows():
            if abs(row["amount"]) > mean + 2 * std:
                anomalies.append({
                    "date": row["date"],
                    "description": row["description"],
                    "amount": abs(row["amount"]),
                    "category": cat,
                    "mean": mean,
                    "ratio": abs(row["amount"]) / mean if mean > 0 else 0,
                })

    return sorted(anomalies, key=lambda x: x["ratio"], reverse=True)


def category_trends(df: pd.DataFrame, ref_month: str = None) -> list:
    """Identifica tendências: categorias que mais cresceram/diminuíram."""
    if df.empty:
        return []

    current_month = ref_month or date.today().strftime("%Y-%m")
    ref_year, ref_mon = map(int, current_month.split("-"))
    if ref_mon == 1:
        prev_month = f"{ref_year - 1}-12"
    else:
        prev_month = f"{ref_year}-{ref_mon - 1:02d}"

    expenses = df[df["amount"] < 0].copy()
    curr = expenses[expenses["year_month"] == current_month]
    prev = expenses[expenses["year_month"] == prev_month]

    curr_by_cat = curr.groupby("category_name")["amount"].sum().abs()
    prev_by_cat = prev.groupby("category_name")["amount"].sum().abs()

    trends = []
    all_cats = set(curr_by_cat.index) | set(prev_by_cat.index)
    for cat in all_cats:
        curr_val = curr_by_cat.get(cat, 0)
        prev_val = prev_by_cat.get(cat, 0)
        if prev_val > 0:
            change_pct = ((curr_val - prev_val) / prev_val) * 100
        elif curr_val > 0:
            change_pct = 100
        else:
            continue

        trends.append({
            "category": cat,
            "current": curr_val,
            "previous": prev_val,
            "change_pct": change_pct,
        })

    return sorted(trends, key=lambda x: abs(x["change_pct"]), reverse=True)


def generate_insights(df: pd.DataFrame, ref_month: str = None) -> list:
    """Gera insights textuais sobre os gastos."""
    insights = []

    if df.empty:
        return [{"icon": "info-circle", "text": "Importe seus extratos para ver insights!", "type": "info"}]

    current_month = ref_month or date.today().strftime("%Y-%m")
    kpis = current_month_kpis(df, current_month)

    # 1. Projeção mensal
    if kpis["projecao_mensal"] > 0:
        insights.append({
            "icon": "chart-line",
            "text": f"Projeção para {current_month}: R$ {kpis['projecao_mensal']:,.2f} em gastos.",
            "type": "info",
        })

    # 2. Variação vs mês anterior
    if kpis["variacao_gastos"] > 10:
        insights.append({
            "icon": "arrow-up",
            "text": f"Gastos aumentaram {kpis['variacao_gastos']:.1f}% em relação ao mês anterior.",
            "type": "warning",
        })
    elif kpis["variacao_gastos"] < -10:
        insights.append({
            "icon": "arrow-down",
            "text": f"Gastos diminuíram {abs(kpis['variacao_gastos']):.1f}% em relação ao mês anterior!",
            "type": "success",
        })

    # 3. Maiores categorias
    breakdown = category_breakdown(df, current_month)
    if not breakdown.empty:
        top_cat = breakdown.iloc[0]
        pct = (top_cat["total"] / breakdown["total"].sum()) * 100
        insights.append({
            "icon": "tag",
            "text": f"'{top_cat['category']}' é a maior despesa: R$ {top_cat['total']:,.2f} ({pct:.0f}% do total).",
            "type": "info",
        })

    # 4. Anomalias
    anomalies = detect_anomalies(df, current_month)
    for a in anomalies[:3]:
        insights.append({
            "icon": "exclamation-triangle",
            "text": f"Gasto atípico em {a['category']}: '{a['description']}' — R$ {a['amount']:,.2f} ({a['ratio']:.1f}x a média).",
            "type": "danger",
        })

    # 5. Tendências
    trends = category_trends(df, current_month)
    for t in trends[:2]:
        if t["change_pct"] > 20:
            insights.append({
                "icon": "trending-up",
                "text": f"'{t['category']}' subiu {t['change_pct']:.0f}%: de R$ {t['previous']:,.2f} para R$ {t['current']:,.2f}.",
                "type": "warning",
            })

    # 6. Saldo
    if kpis["saldo"] < 0:
        insights.append({
            "icon": "exclamation-circle",
            "text": f"Atenção: gastos superam receitas em R$ {abs(kpis['saldo']):,.2f} em {current_month}.",
            "type": "danger",
        })

    # 7. Orçamento estourado
    budget_alerts = check_budget_alerts(df, current_month)
    for alert in budget_alerts:
        insights.append({
            "icon": "wallet",
            "text": alert,
            "type": "warning",
        })

    return insights if insights else [{"icon": "check-circle", "text": "Tudo certo! Gastos controlados.", "type": "success"}]


def _normalize_desc_key(description: str) -> str:
    """Extract a normalized key from a description for grouping recurring transactions."""
    import unicodedata
    text = description.lower().strip()
    nfkd = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Remove common prefixes like "Transferencia enviada pelo Pix - "
    import re
    text = re.sub(r"^(transferencia (enviada|recebida) pelo pix\s*-\s*)", "", text)
    text = re.sub(r"^(pagamento de boleto efetuado\s*-\s*)", "", text)
    text = re.sub(r"^(compra no debito\s*-\s*)", "", text)
    # Take first 3-4 significant words
    words = [w for w in text.split() if len(w) > 2]
    return " ".join(words[:4])


def pivot_by_category_month(df: pd.DataFrame, months: int = 6) -> dict:
    """Creates a pivot table: categories as rows, months as columns.

    Returns:
    {
        "months": ["2026-01", "2026-02", ...],
        "categories": [
            {"name": "Mercado", "color": "#FF6384", "values": {"2026-01": 500.0, ...}, "total": 800.0},
            ...
        ],
        "month_totals": {"2026-01": 5000.0, "2026-02": 4500.0},
        "grand_total": 9500.0
    }
    """
    if df.empty:
        return {"months": [], "categories": [], "month_totals": {}, "grand_total": 0}

    expenses = df[df["amount"] < 0].copy()
    if expenses.empty:
        return {"months": [], "categories": [], "month_totals": {}, "grand_total": 0}

    expenses["abs_amount"] = expenses["amount"].abs()

    # Get the last N months
    all_months = sorted(expenses["year_month"].unique())
    selected_months = all_months[-months:] if len(all_months) > months else all_months

    expenses = expenses[expenses["year_month"].isin(selected_months)]

    # Pivot
    pivot = expenses.groupby(["category_name", "category_color", "year_month"])["abs_amount"].sum().reset_index()

    categories = []
    for (cat_name, cat_color), group in pivot.groupby(["category_name", "category_color"]):
        values = {}
        for _, row in group.iterrows():
            values[row["year_month"]] = round(row["abs_amount"], 2)
        total = round(sum(values.values()), 2)
        categories.append({
            "name": cat_name,
            "color": cat_color,
            "values": values,
            "total": total,
        })

    # Sort by total descending
    categories.sort(key=lambda x: x["total"], reverse=True)

    # Month totals
    month_totals = {}
    for m in selected_months:
        month_totals[m] = round(expenses[expenses["year_month"] == m]["abs_amount"].sum(), 2)

    grand_total = round(sum(month_totals.values()), 2)

    return {
        "months": list(selected_months),
        "categories": categories,
        "month_totals": month_totals,
        "grand_total": grand_total,
    }


def detect_recurring_transactions(df: pd.DataFrame, months_back: int = 12) -> list[dict]:
    """Detect transactions that appear monthly with similar descriptions.

    Returns list of dicts with:
    - pattern: str (the recurring description/vendor pattern)
    - category_name: str
    - avg_amount: float
    - frequency: int (how many months it appeared)
    - last_seen: str (YYYY-MM)
    - months_seen: list[str]
    - is_missing_current: bool (didn't appear this month)
    - amount_changed: bool (latest amount differs >20% from average)
    """
    if df.empty:
        return []

    expenses = df[df["amount"] < 0].copy()
    if expenses.empty:
        return []

    expenses["desc_key"] = expenses["description"].apply(_normalize_desc_key)

    # Group by normalized key
    results = []
    current_month = date.today().strftime("%Y-%m")

    for key, group in expenses.groupby("desc_key"):
        if not key or len(key) < 3:
            continue

        months_seen = sorted(group["year_month"].unique())
        if len(months_seen) < 3:
            continue

        avg_amount = abs(group["amount"].mean())
        last_seen = months_seen[-1]
        latest_amount = abs(group[group["year_month"] == last_seen]["amount"].mean())
        amount_changed = abs(latest_amount - avg_amount) / avg_amount > 0.2 if avg_amount > 0 else False

        # Get the most common category
        cat_name = group["category_name"].mode()
        cat_name = cat_name.iloc[0] if len(cat_name) > 0 else "Outros"

        results.append({
            "pattern": key,
            "category_name": cat_name,
            "avg_amount": round(avg_amount, 2),
            "frequency": len(months_seen),
            "last_seen": last_seen,
            "months_seen": list(months_seen),
            "is_missing_current": current_month not in months_seen,
            "amount_changed": amount_changed,
        })

    # Sort by frequency descending
    results.sort(key=lambda x: x["frequency"], reverse=True)
    return results


def check_budget_alerts(df: pd.DataFrame, month: str) -> list:
    """Verifica se algum orçamento foi ultrapassado."""
    session = get_session()
    budgets = session.query(Budget).filter(Budget.month == month).all()
    session.close()

    if not budgets:
        return []

    expenses = df[(df["amount"] < 0) & (df["year_month"] == month)]
    alerts = []

    for b in budgets:
        cat_info = get_categories().get(b.category_id, {})
        cat_name = cat_info.get("name", "?")

        if b.person:
            cat_expenses = expenses[
                (expenses["category_id"] == b.category_id) & (expenses["person"] == b.person)
            ]["amount"].sum()
        else:
            cat_expenses = expenses[expenses["category_id"] == b.category_id]["amount"].sum()

        spent = abs(cat_expenses)
        pct = (spent / b.limit_amount * 100) if b.limit_amount > 0 else 0

        if pct >= 100:
            alerts.append(
                f"Orçamento de '{cat_name}' estourado! R$ {spent:,.2f} / R$ {b.limit_amount:,.2f} ({pct:.0f}%)."
            )
        elif pct >= 80:
            alerts.append(
                f"Orçamento de '{cat_name}' em alerta: R$ {spent:,.2f} / R$ {b.limit_amount:,.2f} ({pct:.0f}%)."
            )

    return alerts
