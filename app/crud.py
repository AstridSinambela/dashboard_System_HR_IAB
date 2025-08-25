from typing import Optional
from sqlalchemy.orm import Session
from .models import TMOperator, CertificationRecord, EvaluationDocument
from datetime import datetime


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
    db: Session, nik: str, certification_type: str, base64_str: str
) -> CertificationRecord:
    record = get_certification_record(db, nik)
    if not record:
        raise ValueError("Certification record not found")

    if certification_type == "Soldering":
        record.file_soldering = base64_str
    elif certification_type == "Screwing":
        record.file_screwing = base64_str
    elif certification_type == "MSA":
        record.file_msa = base64_str
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

# -------------------- Evaluation Document --------------------
def save_evaluation_document(db: Session, data: dict) -> EvaluationDocument:
    mapped_data = {
        "nik": data["nik"],
        "eval_number": data["eval_number"],
        "op_train_eval": data["file_op_train_eval"],
        "op_skills_eval": data["file_op_skills_eval"],
        "train_eval": data["file_train_eval"],
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
    """
    Ambil certification record terakhir berdasarkan created_at (descending).
    """
    return (
        db.query(CertificationRecord)
        .filter(CertificationRecord.nik == nik)
        .order_by(CertificationRecord.created_at.desc())
        .first()
    )

# -------------------- Evaluation Document --------------------
def get_latest_evaluation_document(db: Session, nik: str) -> Optional[EvaluationDocument]:
    """
    Ambil evaluation document terakhir berdasarkan upload_date (descending).
    """
    return (
        db.query(EvaluationDocument)
        .filter(EvaluationDocument.nik == nik)
        .order_by(EvaluationDocument.upload_date.desc())
        .first()
    )

