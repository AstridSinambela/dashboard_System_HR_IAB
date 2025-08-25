from sqlalchemy import Column, String, Integer, Date, Numeric, DateTime, LargeBinary, ForeignKey
from datetime import datetime
from .database import Base
from pydantic import BaseModel, Field
from sqlalchemy import Column, Text
from sqlalchemy.dialects.mssql import CHAR
from sqlalchemy.orm import relationship
from typing import Optional

class TMOperator(Base):
    __tablename__ = "TM_Operator"
    nik = Column("NIK", String(8), primary_key=True, index=True)
    name = Column("Name", String(50), nullable=False)
    line = Column("Line", String(20), nullable=False)
    contract_status = Column("ContractStatus", String(10))
    end_contract_date = Column("EndContractDate", Date)
    level = Column("Level", String(50))
    photo = Column("Photo", LargeBinary)  # image column

class CertificationRecord(Base):
    __tablename__ = "T_CertificationRecord"

    id = Column("ID", Integer, primary_key=True, index=True)
    nik = Column("NIK", String(8), ForeignKey("TM_Operator.NIK"), nullable=False)

    soldering_written = Column("SolderingWritten", Integer, nullable=False)
    soldering_practical = Column("SolderingPractical", Integer, nullable=False)
    soldering_result = Column("SolderingResult", String(10), nullable=False)

    screwing_technique = Column("ScrewingTechnique", Integer, nullable=False)
    screwing_work = Column("ScrewingWork", Integer, nullable=False)
    screwing_result = Column("ScrewingResult", String(10), nullable=False)

    ds_tiu = Column("DS_TIU", Integer, nullable=False)
    ds_accu = Column("DS_Accu", Integer, nullable=False)
    ds_heco = Column("DS_Heco", Integer, nullable=False)
    ds_mcc = Column("DS_MCC", Integer, nullable=False)
    ds_result = Column("DS_Result", String(10), nullable=False)

    process = Column("Process", String(100), nullable=False)
    ls_target = Column("LS_Target", Numeric(5,2), nullable=False)
    ls_actual = Column("LS_Actual", Numeric(5,2), nullable=False)
    ls_achievement = Column("LS_Achievement", Numeric(5,2), nullable=False)
    ls_result = Column("LS_Result", String(10), nullable=False)

    msaa_accuracy = Column("MSAA_Accuracy", Integer, nullable=False)
    msaa_missrate = Column("MSAA_MissRate", Integer, nullable=False)
    msaa_falsealarm = Column("MSAA_FalseAlarm", Integer, nullable=False)
    msaa_confidence = Column("MSAA_Confidence", Integer, nullable=False)
    msaa_result = Column("MSAA_Result", String(10), nullable=False)

    soldering_docno = Column("SolderingDocNo", String(50), nullable=False)
    soldering_traindate = Column("SolderingTrainDate", Date, nullable=False)
    soldering_expdate = Column("SolderingExpDate", Date, nullable=False)

    screwing_docno = Column("ScrewingDocNo", String(50), nullable=False)
    screwing_traindate = Column("ScrewingTrainDate", Date, nullable=False)
    screwing_expdate = Column("ScrewingExpiredDate", Date, nullable=False)

    msa_docno = Column("MSADocNo", String(50), nullable=False)
    msa_traindate = Column("MSATrainDate", Date, nullable=False)
    msa_expdate = Column("MSAExpDate", Date, nullable=False)
    
    file_soldering = Column("FileSoldering", Text, nullable=False)
    file_screwing = Column("FileScrewing", Text, nullable=False)
    file_msa = Column("FileMSA", Text, nullable=False)
    
    status = Column("Status", String(20), nullable=False)

    created_at = Column("CreatedAt", DateTime, nullable=False, default=datetime.utcnow)

class EvaluationDocument(Base):
    __tablename__ = "T_EvaluationDocument"

    id = Column("ID", Integer, primary_key=True, autoincrement=True, index=True)
    nik = Column("NIK", CHAR(8), ForeignKey("TM_Operator.NIK"), nullable=False)
    upload_date = Column("UploadDate", Date, nullable=False, default=datetime.utcnow)
    op_train_eval = Column("OpTrainEval", Text, nullable=False)
    op_skills_eval = Column("OpSkillsEval", Text, nullable=False)
    train_eval = Column("TrainEval", Text, nullable=False)
    eval_number = Column("EvalNumber", String(50), nullable=False)
    # operator = relationship("TMOperator", back_populates="certification_documents")