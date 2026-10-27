from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import Transaction, ImportLog
from parsers.ofx_parser import parse_ofx
from parsers.csv_parser import parse_csv
from categorizer.engine import categorize_transactions

router = APIRouter(prefix="/api/upload", tags=["upload"])


def _parse_file(content: bytes, filename: str, person: str, bank: str):
    """Parse file based on extension."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "ofx":
        df = parse_ofx(content, person, bank)
        detected_bank = df["bank"].iloc[0] if not df.empty else bank
    elif ext == "csv":
        df = parse_csv(content, person, bank)
        detected_bank = df["bank"].iloc[0] if not df.empty else bank
    else:
        raise HTTPException(400, f"Formato não suportado: .{ext}. Use .ofx ou .csv")
    return df, detected_bank


def _check_duplicates(df, db: Session):
    """Split DataFrame into new and duplicate transactions."""
    if df.empty:
        return df, 0

    hashes = df["import_hash"].tolist()
    existing = set(
        h[0] for h in db.query(Transaction.import_hash)
        .filter(Transaction.import_hash.in_(hashes))
        .all()
    )

    mask = ~df["import_hash"].isin(existing)
    new_df = df[mask].copy()
    dup_count = len(df) - len(new_df)
    return new_df, dup_count


@router.post("/preview")
async def upload_preview(
    file: UploadFile = File(...),
    person: str = Form(...),
    bank: str = Form("Auto"),
    db: Session = Depends(get_db),
):
    content = await file.read()
    if not content:
        raise HTTPException(400, "Arquivo vazio")

    try:
        df, detected_bank = _parse_file(content, file.filename, person, bank)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(400, f"Erro ao processar arquivo: {str(e)}")

    if df.empty:
        return {
            "filename": file.filename,
            "bank": detected_bank,
            "new_count": 0,
            "dup_count": 0,
            "transactions": [],
        }

    # Categorize
    df = categorize_transactions(df)

    # Check duplicates
    new_df, dup_count = _check_duplicates(df, db)

    # Prepare preview (first 100)
    preview_df = new_df.head(100).copy()
    preview = []
    for _, row in preview_df.iterrows():
        preview.append({
            "date": str(row["date"]),
            "description": row["description"],
            "amount": float(row["amount"]),
            "person": row["person"],
            "bank": row["bank"],
            "category_id": int(row["category_id"]) if row.get("category_id") is not None else None,
            "category_name": row.get("category_name", ""),
            "import_hash": row["import_hash"],
        })

    return {
        "filename": file.filename,
        "bank": detected_bank,
        "new_count": len(new_df),
        "dup_count": dup_count,
        "transactions": preview,
    }


@router.post("/confirm")
async def upload_confirm(
    file: UploadFile = File(...),
    person: str = Form(...),
    bank: str = Form("Auto"),
    db: Session = Depends(get_db),
):
    content = await file.read()
    if not content:
        raise HTTPException(400, "Arquivo vazio")

    try:
        df, detected_bank = _parse_file(content, file.filename, person, bank)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(400, f"Erro ao processar arquivo: {str(e)}")

    if df.empty:
        return {"imported": 0, "message": "Nenhuma transação encontrada no arquivo"}

    # Categorize
    df = categorize_transactions(df)

    # Filter duplicates
    new_df, dup_count = _check_duplicates(df, db)

    if new_df.empty:
        return {"imported": 0, "message": "Todas as transações já foram importadas anteriormente"}

    # Insert new transactions
    count = 0
    for _, row in new_df.iterrows():
        txn = Transaction(
            date=row["date"],
            description=row["description"],
            amount=float(row["amount"]),
            category_id=int(row["category_id"]) if row.get("category_id") is not None else None,
            person=row["person"],
            bank=row["bank"],
            import_hash=row["import_hash"],
        )
        db.add(txn)
        count += 1

    # Create import log
    log = ImportLog(
        filename=file.filename,
        record_count=count,
        bank=detected_bank,
        person=person,
    )
    db.add(log)
    db.commit()

    return {
        "imported": count,
        "duplicates_skipped": dup_count,
        "message": f"{count} transação(ões) importada(s) com sucesso",
    }
