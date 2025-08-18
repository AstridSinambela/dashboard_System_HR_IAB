from sqlalchemy.orm import Session
from .models import TMOperator, CertificationRecord,EvaluationDocument
from app import models

def get_operator(db: Session, nik: str):
    nik = nik.strip() 
    return db.query(TMOperator).filter(TMOperator.nik == nik).first()

def create_certification_record(db: Session, record_data: dict):
    record = CertificationRecord(**record_data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def update_certification_filepath(db: Session, certification_type: str, data: dict):
    record = (
        db.query(models.CertificationRecord)
        .filter(models.CertificationRecord.NIK == data["NIK"])
        .order_by(models.CertificationRecord.CreatedAt.desc())
        .first()
    )
    if not record:
        raise ValueError("Certification record not found")

    record.DocumentNumber = data["DocumentNumber"]
    record.FilePath = data["FilePath"]
    record.Status = data["Status"]
    record.TrainingDate = data["TrainingDate"]
    record.ExpiredDate = data["ExpiredDate"]

    db.commit()

# Update Status Form
def has_certification_record(db: Session, nik: str) -> bool:
    return db.query(CertificationRecord).filter(CertificationRecord.nik == nik).first() is not None

# Save Certification Document
def save_evaluation_document(db: Session, data: dict):
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