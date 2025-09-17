from datetime import datetime
from sqlalchemy import CHAR, Column, Date, ForeignKey, Integer, LargeBinary, Numeric, String, DateTime, Text
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "T_user"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    firstname = Column(String(50))
    lastname = Column(String(50))
    fullname = Column(String(100))
    gender = Column(Integer)  # 0/1
    role_id = Column(Integer)  # 1=admin, 2=hr, 3=
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

class TMOperator(Base):
    __tablename__ = "TM_Operator"
    nik = Column("NIK", CHAR(8), primary_key=True, index=True)
    name = Column("Name", String(50), nullable=False)
    line = Column("Line", String(20), nullable=False)
    contract_status = Column("ContractStatus", String(10))
    end_contract_date = Column("EndContractDate", Date)
    level = Column("Level", String(50))
    photo = Column("Photo", LargeBinary)

class CertificationRecord(Base):
    __tablename__ = "T_CertificationRecord"

    id = Column("ID", Integer, primary_key=True, index=True)
    nik = Column("NIK", CHAR(8), ForeignKey("TM_Operator.NIK"), nullable=False)

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

class DocumentGroup(Base):
    __tablename__ = "T_DocumentGroup"

    id_cos = Column("id_cos", String(100), primary_key=True, index=True)
    status = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("T_user.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("T_user.id"), nullable=True)
    
class GroupOperator(Base):
    __tablename__ = "T_GroupOperator"
        
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_cos = Column("id_cos", String(100), ForeignKey("T_DocumentGroup.id_cos"), nullable=False)
    pdf_operator_id = Column(Integer, ForeignKey("T_PDFOPT.Id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DocumentForGroup(Base):
    __tablename__ = "T_DocumentForGroup"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_cos = Column(String(100), ForeignKey("T_DocumentGroup.id_cos"), nullable=False)
    doc_type = Column(String(20), nullable=False)   # "COS" | "PFM" | "WGS" | "MO" | "OTHERS"
    file_name = Column(String(255), nullable=False)
    file_content = Column(LargeBinary, nullable=False)
    mime_type = Column(String) 
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey("T_user.id"), nullable=True)
    
class PDFGroupFinal(Base):
    __tablename__ = "T_PDFGroupFinal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_cos = Column(String(100), ForeignKey("T_DocumentGroup.id_cos"), nullable=False)
    final_pdf = Column(LargeBinary, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

class PDFOPT(Base):
    __tablename__ = "T_PDFOPT"

    id = Column("Id", Integer, primary_key=True, index=True)
    nik = Column("NIK", String(8), index=True, nullable=False)
    merged_pdf = Column("MergedPDF", Text, nullable=False)  # kalau sudah varbinary, ganti ke LargeBinary
    created_at = Column("CreatedAt", DateTime, server_default=func.now())

class EvaluationDocumentGroup(Base):
    __tablename__ = "T_EvaluationDocumentGroup"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_pdfFinal = Column(Integer, ForeignKey("T_PDFGroupFinal.id"), nullable=False)

    status = Column(Integer, default=1, nullable=False)
    created_time = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("T_user.id"), nullable=False)   # issuer
    updated_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("T_user.id"), nullable=True)
    update_program = Column(Text, nullable=True)   # info singkat kondisi perubahan stage



class EvalTask(Base):
    __tablename__ = "T_EvalTask"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_eval = Column(Integer, ForeignKey("T_EvaluationDocumentGroup.id"), nullable=False)

    task_type = Column(String(20), nullable=False)
    # "CHECK", "APPROVE", "QA_CHECK", "QA_APPROVE"

    tasked_to = Column(Integer, ForeignKey("T_user.id"), nullable=False)  # user yang bertugas
    status = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EvalRevision(Base):
    __tablename__ = "T_EvalRevision"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("T_EvalTask.id"), nullable=False)
    description = Column(Text, nullable=False)
    file_name = Column(String(255))
    file_content = Column(LargeBinary)
    mime_type = Column(String(50))
    status = Column(Integer, default=1)  # 1=New, 2=Waiting Check, 3=Done
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("T_user.id"), nullable=False)
    give_to = Column(Integer, ForeignKey("T_user.id"), nullable=True)
