from pydantic import BaseModel, validator
from datetime import date, datetime
from typing import Optional

# ================= Operator List (untuk popup search) =================
class OperatorListSchema(BaseModel):
    nik: str
    name: str

    class Config:
        from_attributes = True

class OperatorServerSideResponse(BaseModel):
    recordsTotal: int
    recordsFiltered: int
    data: list[OperatorListSchema]

class CertificationRecordSchema(BaseModel):
    id: int
    nik: str

    soldering_written: int
    soldering_practical: int
    soldering_result: str

    screwing_technique: int
    screwing_work: int
    screwing_result: str

    ds_tiu: int
    ds_accu: int
    ds_heco: int
    ds_mcc: int
    ds_result: str

    process: str
    ls_target: float
    ls_actual: float
    ls_achievement: float
    ls_result: str

    msaa_accuracy: int
    msaa_missrate: int
    msaa_falsealarm: int
    msaa_confidence: int
    msaa_result: str

    soldering_docno: str
    soldering_traindate: date
    soldering_expdate: date

    screwing_docno: str
    screwing_traindate: date
    screwing_expdate: date

    msa_docno: str
    msa_traindate: date
    msa_expdate: date

    file_soldering: str
    file_screwing: str
    file_msa: str

    status: str
    created_at: datetime

    class Config:
        from_attributes = True

    @validator(
            "soldering_traindate", "soldering_expdate",
            "screwing_traindate", "screwing_expdate",
            "msa_traindate", "msa_expdate",
            pre=True
        )
    def parse_dates(cls, value):
            if isinstance(value, str):
                try:
                    # parse MM/DD/YYYY
                    return datetime.strptime(value, "%m/%d/%Y").date()
                except ValueError:
                    raise ValueError("Tanggal harus format MM/DD/YYYY")
            return value


class CreateCertificationRecordSchema(BaseModel):
    nik: str

    soldering_written: int
    soldering_practical: int
    soldering_result: str

    screwing_technique: int
    screwing_work: int
    screwing_result: str

    ds_tiu: int
    ds_accu: int
    ds_heco: int
    ds_mcc: int
    ds_result: str

    process: str
    ls_target: float
    ls_actual: float
    ls_achievement: float
    ls_result: str

    msaa_accuracy: int
    msaa_missrate: int
    msaa_falsealarm: int
    msaa_confidence: int
    msaa_result: str

    soldering_docno: str
    soldering_traindate: date
    soldering_expdate: date

    screwing_docno: str
    screwing_traindate: date
    screwing_expdate: date

    msa_docno: str
    msa_traindate: date
    msa_expdate: date

    file_soldering: str
    file_screwing: str
    file_msa: str

    status: str

    @validator(
            "soldering_traindate", "soldering_expdate",
            "screwing_traindate", "screwing_expdate",
            "msa_traindate", "msa_expdate",
            pre=True
        )
    def parse_dates(cls, value):
            if isinstance(value, str):
                try:
                    # parse MM/DD/YYYY
                    return datetime.strptime(value, "%m/%d/%Y").date()
                except ValueError:
                    raise ValueError("Tanggal harus format MM/DD/YYYY")
            return value


class UpdateCertificationRecordSchema(BaseModel):
    nik: Optional[str]

    soldering_written: Optional[int]
    soldering_practical: Optional[int]
    soldering_result: Optional[str]

    screwing_technique: Optional[int]
    screwing_work: Optional[int]
    screwing_result: Optional[str]

    ds_tiu: Optional[int]
    ds_accu: Optional[int]
    ds_heco: Optional[int]
    ds_mcc: Optional[int]
    ds_result: Optional[str]

    process: Optional[str]
    ls_target: Optional[float]
    ls_actual: Optional[float]
    ls_achievement: Optional[float]
    ls_result: Optional[str]

    msaa_accuracy: Optional[int]
    msaa_missrate: Optional[int]
    msaa_falsealarm: Optional[int]
    msaa_confidence: Optional[int]
    msaa_result: Optional[str]

    soldering_docno: Optional[str]
    soldering_traindate: Optional[date]
    soldering_expdate: Optional[date]

    screwing_docno: Optional[str]
    screwing_traindate: Optional[date]
    screwing_expdate: Optional[date]

    msa_docno: Optional[str]
    msa_traindate: Optional[date]
    msa_expdate: Optional[date]

    file_soldering: Optional[str]
    file_screwing: Optional[str]
    file_msa: Optional[str]

    status: Optional[str]

# ================= Evaluation Document =================
class EvaluationDocumentSchema(BaseModel):
    id: int
    nik: str
    op_train_eval: Optional[str]   # sudah berupa data URI PDF
    op_skills_eval: Optional[str]
    train_eval: Optional[str]
    upload_date: Optional[date]          # ISO format string

    class Config:
        from_attributes = True 

class OperatorIABSchema(BaseModel):
    nik: str
    name: Optional[str]
    line: Optional[str]
    contract_status: Optional[str]
    end_contract_date: Optional[str]
    level: Optional[str]
    photo: Optional[str]  # base64 image

    soldering_written: Optional[int]
    soldering_practical: Optional[int]
    soldering_result: Optional[str]

    screwing_technique: Optional[int]
    screwing_work: Optional[int]
    screwing_result: Optional[str]

    ds_tiu: Optional[int]
    ds_accu: Optional[int]
    ds_heco: Optional[int]
    ds_mcc: Optional[int]
    ds_result: Optional[str]

    process: Optional[str]
    ls_target: Optional[float]
    ls_actual: Optional[float]
    ls_achievement: Optional[float]
    ls_result: Optional[str]

    msaa_accuracy: Optional[int]
    msaa_missrate: Optional[int]
    msaa_falsealarm: Optional[int]
    msaa_confidence: Optional[int]
    msaa_result: Optional[str]

    soldering_docno: Optional[str]
    soldering_traindate: Optional[date]
    soldering_expdate: Optional[date]

    screwing_docno: Optional[str]
    screwing_traindate: Optional[date]
    screwing_expdate: Optional[date]

    msa_docno: Optional[str]
    msa_traindate: Optional[date]
    msa_expdate: Optional[date]

    file_soldering: Optional[str]
    file_screwing: Optional[str]
    file_msa: Optional[str]

    status: Optional[str]

    evaluation: Optional[EvaluationDocumentSchema]

    class Config:
        from_attributes = True

# ================= Save and Merge PDF Input Schema =================
class SaveMergeIn(BaseModel):
    nik: str
    file_soldering: str
    file_screwing: str
    file_msa: str
    op_train_eval: str
    op_skills_eval: str
    train_eval: str
    created_at: Optional[date] = None