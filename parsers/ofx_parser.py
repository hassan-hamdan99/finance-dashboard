import pandas as pd
from ofxparse import OfxParser
import hashlib
import io
import re


def parse_ofx(file_content: bytes, person: str, bank: str = "Auto") -> pd.DataFrame:
    """Parse um arquivo OFX e retorna DataFrame padronizado."""
    ofx = OfxParser.parse(io.BytesIO(file_content))

    rows = []
    for account in _get_accounts(ofx):
        bank_name = bank if bank != "Auto" else _detect_bank_ofx(ofx, account)
        for idx, txn in enumerate(account.statement.transactions):
            if not txn.date or txn.amount is None:
                continue
            desc_raw = txn.memo or txn.payee or ""
            if not desc_raw.strip():
                continue
            desc = _fix_text(desc_raw)
            fitid = getattr(txn, "id", None)
            row = {
                "date": txn.date.date() if hasattr(txn.date, "date") else txn.date,
                "description": _clean_description(desc),
                "amount": float(txn.amount),
                "person": person,
                "bank": bank_name,
                "import_hash": _make_hash(txn.date, desc_raw, txn.amount, person, fitid, idx),
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.sort_values("date").reset_index(drop=True)

        # Filtra transferências internas RDB (Caixinha Nubank)
        rdb_mask = df["description"].str.contains(
            r"aplica[cç][aã]o rdb|resgate rdb", case=False, na=False
        )
        n_filtered = rdb_mask.sum()
        if n_filtered > 0:
            print(f"[OFX] Filtradas {n_filtered} transferências internas (RDB)")
            df = df[~rdb_mask].reset_index(drop=True)

    return df


def _fix_text(text: str) -> str:
    """Corrige texto que pode ter mojibake (UTF-8 lido como latin-1)."""
    try:
        fixed = text.encode("latin-1").decode("utf-8")
        return fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text


def _get_accounts(ofx):
    """Extrai contas do OFX (pode ter múltiplas)."""
    if hasattr(ofx, "accounts"):
        return ofx.accounts
    elif hasattr(ofx, "account"):
        return [ofx.account]
    return []


def _detect_bank_ofx(ofx, account):
    """Tenta detectar o banco pelo OFX."""
    org = ""
    if hasattr(ofx, "signon") and hasattr(ofx.signon, "org"):
        org = _fix_text(ofx.signon.org or "").upper()
    if hasattr(account, "institution") and account.institution:
        org = _fix_text(getattr(account.institution, "organization", "") or "").upper()

    if "NUBANK" in org or "NU PAGAMENTOS" in org:
        return "Nubank"
    elif "ITAU" in org:
        return "Itaú"
    elif "BRADESCO" in org:
        return "Bradesco"
    elif "INTER" in org:
        return "Inter"
    elif "CAIXA" in org:
        return "Caixa"
    elif "BANCO DO BRASIL" in org or "BB" in org:
        return "Banco do Brasil"
    elif "SANTANDER" in org:
        return "Santander"
    return org or "Desconhecido"


def _clean_description(desc: str) -> str:
    """Limpa a descrição da transação."""
    desc = " ".join(desc.split())
    return desc.strip()


def _make_hash(date, description: str, amount, person: str, fitid=None, index=0) -> str:
    """Cria hash único para deduplicação (usa fitid + index como no parser de referência)."""
    parts = [str(date), f"{float(amount):.2f}", description.upper()]
    if fitid:
        parts.append(str(fitid))
    parts.append(str(index))
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()
