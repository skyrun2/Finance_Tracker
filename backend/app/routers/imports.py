import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Account, Import, Transaction
from app.schemas import ClassificationRuleCreate, ClassificationRuleResponse, ImportResponse, ImportDetailResponse
from app.services.etl.pipeline import compute_checksum, process_import, run_pipeline
from app.services.pdf_import.pdf_pipeline import process_pdf, build_preview, confirm_import
from app.config import settings

router = APIRouter(prefix="/api/v1/imports", tags=["imports"])


ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "pdf"}


async def _save_upload(file: UploadFile) -> tuple[str, str, bytes]:
    ext = Path(file.filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format '{ext}' not supported. Use CSV, XLSX, XLS or PDF.",
        )

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4()}.{ext}"
    file_path = upload_dir / unique_name

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum 50MB")

    with open(file_path, "wb") as f:
        f.write(content)

    return unique_name, str(file_path), content


async def _check_duplicate_file(db: AsyncSession, checksum: str) -> bool:
    existing = await db.execute(
        select(Import).where(Import.checksum == checksum, Import.status == "completed")
    )
    return existing.scalar_one_or_none() is not None


async def _create_import_record(
    db: AsyncSession,
    account_id: str,
    filename: str,
    original_filename: str,
    file_type: str,
    checksum: str,
    import_type: str = "bank_statement",
) -> Import:
    record = Import(
        account_id=account_id,
        filename=filename,
        original_filename=original_filename,
        file_type=file_type,
        checksum=checksum,
        status="uploaded",
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


# ─── Bank Statement Import ────────────────────────────────────────────


@router.post("/bank-statement", status_code=status.HTTP_202_ACCEPTED)
async def import_bank_statement(
    file: UploadFile = File(...),
    account_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Import a bank statement CSV/XLSX file."""
    account = await db.get(Account, account_id)
    if not account or not account.is_active:
        raise HTTPException(status_code=404, detail="Account not found")

    unique_name, file_path, content = await _save_upload(file)
    checksum = compute_checksum(file_path)

    if await _check_duplicate_file(db, checksum):
        os.remove(file_path)
        raise HTTPException(status_code=409, detail="This file has already been imported")

    import_record = await _create_import_record(
        db, account_id, unique_name, file.filename, "csv", checksum, "bank_statement"
    )
    print("to hee")
    result = await run_pipeline(db, file_path, account_id, import_record.id)
    await db.refresh(import_record)

    return {
        "import_id": import_record.id,
        "status": import_record.status,
        "summary": {
            "total_parsed": result.total_parsed,
            "saved": result.saved,
            "duplicates": result.duplicates,
            "errors": len(result.errors),
            "persist_errors": len(result.import_errors),
        },
    }


# ─── Credit Card Import ──────────────────────────────────────────────


@router.post("/credit-card", status_code=status.HTTP_202_ACCEPTED)
async def import_credit_card(
    file: UploadFile = File(...),
    account_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Import a credit card invoice (usually from Nubank or similar)."""
    account = await db.get(Account, account_id)
    if not account or not account.is_active:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.type != "CREDIT_CARD":
        raise HTTPException(status_code=400, detail="Account must be of type CREDIT_CARD")

    unique_name, file_path, content = await _save_upload(file)
    checksum = compute_checksum(file_path)

    if await _check_duplicate_file(db, checksum):
        os.remove(file_path)
        raise HTTPException(status_code=409, detail="This file has already been imported")

    import_record = await _create_import_record(
        db, account_id, unique_name, file.filename, file_path.rsplit(".", 1)[-1], checksum, "credit_card"
    )

    result = await run_pipeline(db, file_path, account_id, import_record.id)
    await db.refresh(import_record)

    return {
        "import_id": import_record.id,
        "status": import_record.status,
        "summary": {
            "total_parsed": result.total_parsed,
            "saved": result.saved,
            "duplicates": result.duplicates,
            "errors": len(result.errors),
            "persist_errors": len(result.import_errors),
        },
    }


# ─── PDF Credit Card Import ─────────────────────────────────────────


@router.post("/credit-card/pdf/preview", status_code=status.HTTP_200_OK)
async def preview_credit_card_pdf(
    file: UploadFile = File(...),
    password: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    ext = "pdf"
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4()}.{ext}"
    file_path = upload_dir / unique_name

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum 50MB")

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        invoice = process_pdf(str(file_path), password=password or None)
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=422, detail=f"Error processing PDF: {str(e)}")

    preview = build_preview(invoice)

    return {
        "file_path": str(file_path),
        "preview": {
            "bank": preview.bank,
            "card_last_four": preview.card_last_four,
            "closing_date": preview.closing_date,
            "due_date": preview.due_date,
            "total_amount": preview.total_amount,
            "items_count": preview.items_count,
            "items_sum": preview.items_sum,
            "items": preview.items,
            "warnings": preview.warnings,
            "is_valid": preview.is_valid,
        },
    }


@router.post("/credit-card/pdf/confirm", status_code=status.HTTP_200_OK)
async def confirm_credit_card_pdf(
    file_path: str = Form(...),
    account_id: str = Form(...),
    password: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    account = await db.get(Account, account_id)
    if not account or not account.is_active:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.type != "CREDIT_CARD":
        raise HTTPException(status_code=400, detail="Account must be of type CREDIT_CARD")

    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        invoice = process_pdf(file_path, password=password or None)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error processing PDF: {str(e)}")

    checksum = compute_checksum(file_path)
    if await _check_duplicate_file(db, checksum):
        raise HTTPException(status_code=409, detail="This file has already been imported")

    import_record = await _create_import_record(
        db, account_id, Path(file_path).name, "bill.pdf", "pdf", checksum, "credit_card"
    )

    saved, duplicates, errors = await confirm_import(
        db, invoice, account_id, import_id=import_record.id
    )

    return {
        "import_id": import_record.id,
        "status": "completed" if saved > 0 and not errors else "error",
        "summary": {
            "saved": saved,
            "duplicates": duplicates,
            "errors": errors,
        },
    }


# ─── Legacy Upload (backward compatible) ────────────────────────────


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_file(
    file: UploadFile = File(...),
    account_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    account = await db.get(Account, account_id)
    if not account or not account.is_active:
        raise HTTPException(status_code=404, detail="Account not found")

    ext = Path(file.filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Format not supported. Use CSV, XLSX or XLS")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4()}.{ext}"
    file_path = upload_dir / unique_name

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum 50MB")

    with open(file_path, "wb") as f:
        f.write(content)

    checksum = compute_checksum(str(file_path))

    existing = await db.execute(
        select(Import).where(Import.checksum == checksum, Import.status == "completed")
    )
    if existing.scalar_one_or_none():
        os.remove(file_path)
        raise HTTPException(status_code=409, detail="This file has already been imported")

    import_record = Import(
        account_id=account_id,
        filename=unique_name,
        original_filename=file.filename,
        file_type=ext,
        checksum=checksum,
        status="uploaded",
    )
    db.add(import_record)
    await db.commit()
    await db.refresh(import_record)

    await process_import(import_record.id, str(file_path), ext, account_id, db)

    return {"import_id": import_record.id, "status": "processing"}


# ─── List & Detail ────────────────────────────────────────────────────


@router.get("")
async def list_imports(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    total = await db.scalar(select(func.count(Import.id)))
    result = await db.execute(
        select(Import)
        .order_by(Import.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    imports = result.scalars().all()

    # Attach transaction count per import
    import_ids = [imp.id for imp in imports]
    if import_ids:
        count_result = await db.execute(
            select(Transaction.import_id, func.count(Transaction.id).label("count"))
            .where(Transaction.import_id.in_(import_ids))
            .group_by(Transaction.import_id)
        )
        counts = {row[0]: row[1] for row in count_result}
    else:
        counts = {}

    data = []
    for imp in imports:
        d = {
            "id": imp.id,
            "account_id": imp.account_id,
            "filename": imp.original_filename,
            "file_type": imp.file_type,
            "status": imp.status,
            "total_rows": imp.total_rows,
            "processed_rows": imp.processed_rows,
            "error_rows": imp.error_rows,
            "summary": imp.summary,
            "created_at": imp.created_at,
            "completed_at": imp.completed_at,
            "transaction_count": counts.get(imp.id, 0),
        }
        data.append(d)

    return {"data": data, "total": total, "page": page, "per_page": per_page}


@router.get("/{import_id}")
async def get_import(import_id: str, db: AsyncSession = Depends(get_db)):
    import_record = await db.get(Import, import_id)
    if not import_record:
        raise HTTPException(status_code=404, detail="Import not found")

    # Get transactions from this import
    txn_result = await db.execute(
        select(Transaction).where(Transaction.import_id == import_id)
    )
    transactions = txn_result.scalars().all()

    return {
        "id": import_record.id,
        "account_id": import_record.account_id,
        "filename": import_record.original_filename,
        "file_type": import_record.file_type,
        "status": import_record.status,
        "total_rows": import_record.total_rows,
        "processed_rows": import_record.processed_rows,
        "error_rows": import_record.error_rows,
        "error_log": import_record.error_log,
        "summary": import_record.summary,
        "created_at": import_record.created_at,
        "completed_at": import_record.completed_at,
        "transaction_count": len(transactions),
    }
