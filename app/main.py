from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi import UploadFile, File, Form, Body
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from app import models, crud
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
import base64
import os
import shutil
import json


Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})



@app.get("/home", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/IAB", response_class=HTMLResponse)
def IAB_page(request: Request):
    return templates.TemplateResponse("IAB.html", {"request": request})

@app.get("/api/operator/hrd", response_class=JSONResponse)
def api_get_operator(nik: str, db: Session = Depends(get_db)):
    op = crud.get_operator(db, nik)
    if not op:
        raise HTTPException(status_code=404, detail="Operator not found.")
    
    #Status Form
    form_status = "Closed" if crud.has_certification_record(db, nik) else "New"
    
    print(f"NIK: {nik}, has_cert_record: {crud.has_certification_record(db, nik)}, form_status: {form_status}")

    photo_base64 = None
    if op.photo:
        photo_base64 = base64.b64encode(op.photo).decode("utf-8")
    
    data = {
        "nik": op.nik,
        "name": op.name,
        "line": op.line,
        "job_level": op.level,
        "contract_status": op.contract_status,
        "end_contract_date": op.end_contract_date.isoformat() if op.end_contract_date else None,
        "Photo": photo_base64,
        "form_status": form_status
    }
    return JSONResponse(content=data)

@app.get("/api/operator/photo")
def api_get_photo(nik: str, db: Session = Depends(get_db)):
    op = crud.get_operator(db, nik)
    if not op or not op.photo:
        raise HTTPException(status_code=404, detail="Photo not found.")
    return Response(content=op.photo, media_type="image/jpeg")

class CertificationRecordIn(BaseModel):
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

    document_number: str
    file_soldering: str
    file_screwing: str
    file_msa: str
    status: str
    training_date: date
    expired_date: date

@app.post("/api/certification")
def create_certification(data: CertificationRecordIn, db: Session = Depends(get_db)):
    crud.create_certification_record(db, data.dict(by_alias=True))
    return {"message": "Certification record created successfully"}

@app.post("/api/certification/upload")
def upload_certification_file(payload: dict = Body(...), db: Session = Depends(get_db)):
    nik = payload["nik"]
    cert_type = payload["certification_type"]
    file_base64 = payload["file_base64"]

    column_map = {
        "Soldering": "file_soldering",
        "Screwing": "file_screwing",
        "MSA": "file_msa"
    }

    column_name = column_map.get(cert_type)
    if not column_name:
        raise HTTPException(status_code=400, detail="Invalid certification type")

    # Dapatkan record
    record = db.query(models.CertificationRecord).filter_by(nik=nik).first()
    if not record:
        raise HTTPException(status_code=404, detail="Certification record not found")

    # Set kolom base64
    setattr(record, column_name, file_base64)
    db.commit()

    return {"message": f"{cert_type} file saved to database as base64"}


# API to get operator data (IAB_Page)
@app.get("/api/operator/iab", response_class=JSONResponse)
def api_get_operator_iab(nik: Optional[str] = None, db: Session = Depends(get_db)):
    if not nik:
        return JSONResponse(content={"form_status": "Waiting"})

    op = crud.get_operator(db, nik)
    if not op:
        return JSONResponse(content={"form_status": "Waiting"})

    # Cek apakah ada data di CertificationRecord
    has_cert = crud.has_certification_record(db, nik)

    # Cek apakah file evaluasi sudah lengkap
    eval_doc = db.query(models.EvaluationDocument).filter_by(nik=nik).first()
    has_eval_complete = (
        eval_doc is not None and
        eval_doc.op_train_eval and
        eval_doc.op_skills_eval and
        eval_doc.train_eval and
        eval_doc.eval_number
    )

    if has_eval_complete:
        form_status = "Closed"
    elif has_cert:
        form_status = "New"
    else:
        form_status = "Waiting"

    photo_base64 = base64.b64encode(op.photo).decode("utf-8") if op.photo else None

    return JSONResponse(content={
        "nik": op.nik,
        "name": op.name,
        "line": op.line,
        "job_level": op.level,
        "contract_status": op.contract_status,
        "end_contract_date": op.end_contract_date.isoformat() if op.end_contract_date else None,
        "Photo": photo_base64,
        "form_status": form_status
    })


# API to get certification data by NIK (IAB_Page)
@app.get("/api/certification", response_class=JSONResponse)
def api_get_certification(nik: str, db: Session = Depends(get_db)):
    cert = db.query(models.CertificationRecord).filter_by(nik=nik).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certification record not found.")

    data = {
        # Screwing
        "screwing_technique": cert.screwing_technique,
        "screwing_work": cert.screwing_work,
        "screwing_result": cert.screwing_result,

        # Soldering
        "soldering_written": cert.soldering_written,
        "soldering_practical": cert.soldering_practical,
        "soldering_result": cert.soldering_result,

        # Line Simulation
        "process": cert.process,
        "ls_target": float(cert.ls_target),
        "ls_actual": float(cert.ls_actual),
        "ls_achievement": float(cert.ls_achievement),
        "ls_result": cert.ls_result,

        # Data Screening
        "ds_tiu": cert.ds_tiu,
        "ds_accu": cert.ds_accu,
        "ds_heco": cert.ds_heco,
        "ds_mcc": cert.ds_mcc,
        "ds_result": cert.ds_result,

        # MSA Assessment
        "msaa_accuracy": cert.msaa_accuracy,
        "msaa_missrate": cert.msaa_missrate,
        "msaa_falsealarm": cert.msaa_falsealarm,
        "msaa_confidence": cert.msaa_confidence,
        "msaa_result": cert.msaa_result,

        # Certification Skills
        "document_number": cert.document_number,
        "file_soldering": cert.file_soldering,
        "file_screwing": cert.file_screwing,
        "file_msa": cert.file_msa,
        "status": cert.status,
        "training_date": cert.training_date.isoformat() if cert.training_date else None,
        "expired_date": cert.expired_date.isoformat() if cert.expired_date else None
    }

    return JSONResponse(content=data)

# API to update certification Document 
class EvaluationSaveIn(BaseModel):
    nik: str
    eval_number: str
    file_op_train_eval: str  # base64
    file_op_skills_eval: str  # base64
    file_train_eval: str  # base64
    upload_date: date = Field(default_factory=lambda: datetime.utcnow().date())
    
    @validator("file_op_train_eval", "file_op_skills_eval", "file_train_eval")
    def validate_base64(cls, v):
        try:
            base64.b64decode(v)
        except Exception:
            raise ValueError("Invalid base64 file input")
        return v

@app.post("/api/evaluation/save")
def save_evaluation_document(data: EvaluationSaveIn, db: Session = Depends(get_db)):
    try:
        print("Received raw data:", json.dumps(data.dict(), indent=2, default=str))
        payload = data.dict()
        result = crud.save_evaluation_document(db, data.dict())
        print("Saved document ID:", result.id)
        return {"message": "Evaluation document saved successfully"}
    except Exception as e:
        print("Error when save evaluation document:", e)
        raise HTTPException(status_code=500, detail=str(e))
