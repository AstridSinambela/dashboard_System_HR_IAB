from typing import Optional
from fastapi import FastAPI, Response, HTTPException
from sqlalchemy.orm import Session
from .models import TMOperator, CertificationRecord, EvaluationDocument, PDFOPT
from datetime import datetime
from PyPDF2 import PdfMerger
from sqlalchemy import or_, asc, desc
from io import BytesIO
import base64
from . import models, schemas

# -------------------- Operator List with Pagination and Search --------------------
def list_operator(
    db: Session,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    query = db.query(TMOperator.nik, TMOperator.name).order_by(TMOperator.name.asc())
    if q:
        query = query.filter(
            or_(
                TMOperator.nik.ilike(f"%{q}%"),
                TMOperator.name.ilike(f"%{q}%"),
            )
        )

    total = query.count()
    items = (
        query.order_by(TMOperator.nik)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return total, items

def list_operators(db: Session, search: str = "", limit: int = None):
    query = db.query(models.TMOperator)
    if search:
        search = f"%{search}%"
        query = query.filter(
            (models.TMOperator.nik.like(search)) |
            (models.TMOperator.name.like(search))
        )
    if limit:
        query = query.limit(limit)
    return query.all()

def get_operators(db: Session, search: str = "", start: int = 0, length: int = 10, order_col: int = 0, order_dir: str = "asc"):
    query = db.query(TMOperator)

    # Total sebelum filter
    total = query.count()

    if search:
        query = query.filter(
            (TMOperator.nik.ilike(f"%{search}%")) |
            (TMOperator.name.ilike(f"%{search}%"))
        )

    # Total setelah filter
    filtered = query.count()
    # Ordering
    columns = [TMOperator.nik, TMOperator.name]
    order_column = columns[order_col] if order_col < len(columns) else TMOperator.nik

    if order_dir == "desc":
         query = query.order_by(desc(order_column))
    else:
        query = query.order_by(asc(order_column))

    # Pagination
    items = query.offset(start).limit(length).all()

    return total, filtered, items


# -------------------- Operator --------------------
def get_operator(db: Session, nik: str) -> Optional[TMOperator]:
    nik = nik.strip()
    return db.query(TMOperator).filter(TMOperator.nik == nik).first()


def get_certification_record(db: Session, nik: str) -> Optional[CertificationRecord]:
    return db.query(CertificationRecord).filter(CertificationRecord.nik == nik).first()


def create_certification_record(db: Session, record_data: dict) -> CertificationRecord:
    record = CertificationRecord(**record_data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def update_certification_file_base64(
    db: Session,
    nik: str,
    certification_type: str,
    base64_str: str,
    docno: Optional[str] = None,
    traindate: Optional[datetime] = None,
    expdate: Optional[datetime] = None,
) -> CertificationRecord:
    record = get_certification_record(db, nik)
    if not record:
        raise ValueError("Certification record not found")

    if certification_type == "Soldering":
        record.file_soldering = base64_str
        record.soldering_docno = docno
        record.soldering_traindate = traindate
        record.soldering_expdate = expdate
    elif certification_type == "Screwing":
        record.file_screwing = base64_str
        record.screwing_docno = docno
        record.screwing_traindate = traindate
        record.screwing_expdate = expdate
    elif certification_type == "MSA":
        record.file_msa = base64_str
        record.msa_docno = docno
        record.msa_traindate = traindate
        record.msa_expdate = expdate
    else:
        raise ValueError("Invalid certification type")

    db.commit()
    db.refresh(record)
    return record


def has_certification_record(db: Session, nik: str) -> bool:
    return db.query(CertificationRecord).filter(CertificationRecord.nik == nik).first() is not None

# -------------------- Certification --------------------
def get_latest_certification(db: Session, nik: str) -> Optional[CertificationRecord]:
    """Ambil certification record terakhir berdasarkan created_at (descending)."""
    return (
        db.query(CertificationRecord)
        .filter(CertificationRecord.nik == nik)
        .order_by(CertificationRecord.created_at.desc())
        .first()
    )

# -------------------- Utils --------------------
def as_pdf_data_uri(base64_str: Optional[str]) -> Optional[str]:
    """Tambahkan prefix supaya frontend bisa langsung render PDF"""
    if not base64_str:
        return None
    return f"data:application/pdf;base64,{base64_str.strip()}"


# -------------------- Evaluation Document --------------------
def save_evaluation_document(db: Session, data: dict) -> EvaluationDocument:
    mapped_data = {
        "nik": data["nik"],
        "op_train_eval": data["op_train_eval"],
        "op_skills_eval": data["op_skills_eval"],
        "train_eval": data["train_eval"],
        "upload_date": data.get("upload_date"),
    }

    record = EvaluationDocument(**mapped_data)
    db.add(record)
    db.commit()
    db.refresh(record)
    print("Saved document ID:", record.id)
    return record

# -------------------- Certification --------------------
def get_latest_certification(db: Session, nik: str) -> Optional[CertificationRecord]:
    return (
        db.query(CertificationRecord)
        .filter(CertificationRecord.nik == nik)
        .order_by(CertificationRecord.created_at.desc())
        .first()
    )

# -------------------- Evaluation Document --------------------
def get_latest_evaluation_document(db: Session, nik: str) -> Optional[EvaluationDocument]:
    return (
        db.query(EvaluationDocument)
        .filter(EvaluationDocument.nik == nik)
        .order_by(EvaluationDocument.upload_date.desc())
        .first()
    )

# -------------------- Save and Merge PDFOPT --------------------
def save_evaluation_and_merge(db: Session, data: dict):
    
    try:
        # 1. Simpan Evaluation Document
        eval_doc = EvaluationDocument(
            nik=data["nik"],
            op_train_eval=data["op_train_eval"],
            op_skills_eval=data["op_skills_eval"],
            train_eval=data["train_eval"],
            upload_date=data.get("upload_date") or datetime.utcnow().date()
        )
        db.add(eval_doc)
        db.flush()

        merger = PdfMerger()
        files = [
            data["file_soldering"],
            data["file_screwing"],
            data["file_msa"],
            data["op_train_eval"],
            data["op_skills_eval"],
            data["train_eval"],
        ]
        for f in files:
            if not f:
                continue  # ✅ skip kalau kosong
            base64_str = f.split(",")[-1] if "," in f else f
            pdf_bytes = base64.b64decode(base64_str)
            merger.append(BytesIO(pdf_bytes))

        output = BytesIO()
        merger.write(output)
        merger.close()

        merged_bytes = output.getvalue()
        merged_b64 = base64.b64encode(merged_bytes).decode("utf-8")

        # 3. Simpan ke T_PDFOPT
        pdfopt = PDFOPT(
            nik=data["nik"],
            merged_pdf=merged_b64
        )
        db.add(pdfopt)

        # 4. Commit transaksi
        db.commit()
        db.refresh(eval_doc)
        db.refresh(pdfopt)

        return {"eval_id": eval_doc.id, "pdf_id": pdfopt.id}

    except Exception as e:
        db.rollback()
        raise e