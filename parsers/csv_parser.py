import pandas as pd
import hashlib
import io
from datetime import datetime


# Mapeamento de formatos conhecidos de bancos brasileiros
BANK_FORMATS = {
    "nubank": {
        "detect_columns": ["date", "title", "amount"],
        "date_col": "date",
        "desc_col": "title",
        "amount_col": "amount",
        "date_format": "%Y-%m-%d",
        "invert_sign": True,  # Nubank: valores positivos = gastos
    },
    "nubank_alt": {
        "detect_columns": ["Data", "Descrição", "Valor"],
        "date_col": "Data",
        "desc_col": "Descrição",
        "amount_col": "Valor",
        "date_format": "%d/%m/%Y",
        "invert_sign": True,
    },
    "itau": {
        "detect_columns": ["data", "lançamento", "valor"],
        "date_col": "data",
        "desc_col": "lançamento",
        "amount_col": "valor",
        "date_format": "%d/%m/%Y",
        "invert_sign": False,
    },
    "bradesco": {
        "detect_columns": ["Data", "Histórico", "Valor"],
        "date_col": "Data",
        "desc_col": "Histórico",
        "amount_col": "Valor",
        "date_format": "%d/%m/%Y",
        "invert_sign": False,
    },
    "inter": {
        "detect_columns": ["Data", "Descrição", "Valor"],
        "date_col": "Data",
        "desc_col": "Descrição",
        "amount_col": "Valor",
        "date_format": "%d/%m/%Y",
        "invert_sign": False,
    },
    "c6": {
        "detect_columns": ["Data", "Descrição", "Valor (R$)"],
        "date_col": "Data",
        "desc_col": "Descrição",
        "amount_col": "Valor (R$)",
        "date_format": "%d/%m/%Y",
        "invert_sign": False,
    },
}


def parse_csv(file_content: bytes, person: str, bank: str = "Auto") -> pd.DataFrame:
    """Parse um arquivo CSV e retorna DataFrame padronizado."""
    # Tenta diferentes encodings
    text = None
    for encoding in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
        try:
            text = file_content.decode(encoding)
            break
        except (UnicodeDecodeError, AttributeError):
            continue

    if text is None:
        raise ValueError("Não foi possível decodificar o arquivo CSV")

    # Tenta diferentes separadores
    for sep in [",", ";", "\t"]:
        try:
            df_raw = pd.read_csv(io.StringIO(text), sep=sep, dtype=str)
            if len(df_raw.columns) >= 2:
                break
        except Exception:
            continue
    else:
        raise ValueError("Não foi possível ler o CSV com separadores padrão")

    # Detecta o formato do banco
    detected_bank, fmt = _detect_bank_format(df_raw, bank)

    if fmt is None:
        # Formato genérico - tenta inferir colunas
        return _parse_generic(df_raw, person, detected_bank)

    return _parse_with_format(df_raw, fmt, person, detected_bank)


def _detect_bank_format(df: pd.DataFrame, bank_hint: str):
    """Detecta o formato do banco pelas colunas do CSV."""
    columns_lower = [c.strip().lower() for c in df.columns]
    columns_original = [c.strip() for c in df.columns]

    # Se o usuário especificou o banco
    if bank_hint != "Auto":
        bank_key = bank_hint.lower().replace("ú", "u").replace("á", "a")
        for key, fmt in BANK_FORMATS.items():
            if bank_key in key or key in bank_key:
                return bank_hint, fmt

    # Auto-detecção por colunas
    for bank_name, fmt in BANK_FORMATS.items():
        expected = [c.lower() for c in fmt["detect_columns"]]
        if all(e in columns_lower for e in expected):
            pretty_name = bank_name.replace("_alt", "").capitalize()
            if pretty_name == "Nubank":
                pretty_name = "Nubank"
            elif pretty_name == "Itau":
                pretty_name = "Itaú"
            return pretty_name, fmt

        # Tenta match exato (case-sensitive)
        if all(c in columns_original for c in fmt["detect_columns"]):
            pretty_name = bank_name.replace("_alt", "").capitalize()
            return pretty_name, fmt

    return bank_hint if bank_hint != "Auto" else "Desconhecido", None


def _parse_with_format(df: pd.DataFrame, fmt: dict, person: str, bank: str) -> pd.DataFrame:
    """Parse CSV usando formato conhecido."""
    df.columns = [c.strip() for c in df.columns]

    date_col = fmt["date_col"]
    desc_col = fmt["desc_col"]
    amount_col = fmt["amount_col"]

    rows = []
    for _, row in df.iterrows():
        try:
            date_str = str(row[date_col]).strip()
            if not date_str or date_str == "nan":
                continue

            date = _parse_date(date_str, fmt.get("date_format"))
            description = str(row[desc_col]).strip()
            amount = _parse_amount(str(row[amount_col]))

            if fmt.get("invert_sign"):
                amount = -amount

            if description and description != "nan":
                rows.append({
                    "date": date,
                    "description": description,
                    "amount": amount,
                    "person": person,
                    "bank": bank,
                    "import_hash": _make_hash(date, description, amount, person),
                })
        except (ValueError, KeyError):
            continue

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values("date").reset_index(drop=True)
    return result


def _parse_generic(df: pd.DataFrame, person: str, bank: str) -> pd.DataFrame:
    """Tenta inferir colunas de um CSV genérico."""
    df.columns = [c.strip() for c in df.columns]
    columns_lower = {c.lower(): c for c in df.columns}

    # Tenta encontrar coluna de data
    date_col = None
    for candidate in ["data", "date", "dt", "dia"]:
        if candidate in columns_lower:
            date_col = columns_lower[candidate]
            break
    if date_col is None:
        date_col = df.columns[0]  # primeira coluna

    # Tenta encontrar coluna de descrição
    desc_col = None
    for candidate in ["descrição", "descricao", "description", "desc", "titulo", "title",
                       "lançamento", "lancamento", "histórico", "historico", "memo"]:
        if candidate in columns_lower:
            desc_col = columns_lower[candidate]
            break
    if desc_col is None:
        # Pega a coluna com mais texto
        text_cols = [c for c in df.columns if c != date_col]
        if text_cols:
            desc_col = text_cols[0]

    # Tenta encontrar coluna de valor
    amount_col = None
    for candidate in ["valor", "amount", "value", "vlr", "valor (r$)"]:
        if candidate in columns_lower:
            amount_col = columns_lower[candidate]
            break
    if amount_col is None:
        # Pega a última coluna numérica
        for c in reversed(df.columns.tolist()):
            if c not in [date_col, desc_col]:
                amount_col = c
                break

    if not all([date_col, desc_col, amount_col]):
        raise ValueError("Não foi possível identificar as colunas do CSV")

    rows = []
    for _, row in df.iterrows():
        try:
            date_str = str(row[date_col]).strip()
            if not date_str or date_str == "nan":
                continue
            date = _parse_date(date_str)
            description = str(row[desc_col]).strip()
            amount = _parse_amount(str(row[amount_col]))

            if description and description != "nan":
                rows.append({
                    "date": date,
                    "description": description,
                    "amount": amount,
                    "person": person,
                    "bank": bank,
                    "import_hash": _make_hash(date, description, amount, person),
                })
        except (ValueError, KeyError):
            continue

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values("date").reset_index(drop=True)
    return result


def _parse_date(date_str: str, fmt: str = None):
    """Parse de data com múltiplos formatos."""
    if fmt:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass

    for f in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"]:
        try:
            return datetime.strptime(date_str, f).date()
        except ValueError:
            continue

    raise ValueError(f"Formato de data não reconhecido: {date_str}")


def _parse_amount(amount_str: str) -> float:
    """Parse de valor monetário brasileiro."""
    amount_str = amount_str.strip().replace("R$", "").replace(" ", "")

    # Formato brasileiro: 1.234,56
    if "," in amount_str and "." in amount_str:
        if amount_str.rindex(",") > amount_str.rindex("."):
            amount_str = amount_str.replace(".", "").replace(",", ".")
        else:
            amount_str = amount_str.replace(",", "")
    elif "," in amount_str:
        amount_str = amount_str.replace(",", ".")

    return float(amount_str)


def _make_hash(date, description: str, amount: float, person: str) -> str:
    """Cria hash único para deduplicação."""
    raw = f"{date}|{description}|{amount}|{person}"
    return hashlib.sha256(raw.encode()).hexdigest()
