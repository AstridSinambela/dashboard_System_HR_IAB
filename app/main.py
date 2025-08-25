# main.py
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi import UploadFile, File, Form, Body
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from app.schemas import (CreateCertificationRecordSchema, UpdateCertificationRecordSchema, CertificationRecordSchema)
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from app import models, crud, database
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from app import models, crud, schemas
from app.models import TMOperator, CertificationRecord, EvaluationDocument
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import base64
import os
import shutil
import json
import traceback  

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# -------------------- Helper utilities --------------------
def bytes_to_base64_str(b: Optional[bytes]) -> Optional[str]:
    if not b:
        return None
    try:
        return base64.b64encode(b).decode("utf-8")
    except Exception:
        return None

def safe_date_to_iso(d: Optional[date]) -> Optional[str]:
    if not d:
        return None
    try:
        return d.isoformat()
    except Exception:
        return None

def as_pdf_data_uri(possible_b64: Optional[str]) -> Optional[str]:
    if not possible_b64:
        return None
    s = possible_b64.strip()
    if s.startswith("data:"):
        return s
    # assume stored as raw base64 for PDF
    return f"data:application/pdf;base64,{s}"

# Dependency untuk ambil session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----- Helper: Check Login -----
def is_logged_in(request: Request):
    return request.cookies.get("logged_in") == "true"

# ----- Root Redirect to Login -----
@app.get("/", response_class=HTMLResponse)
def root_redirect():
    return RedirectResponse(url="/login")

# ----- Login Page (GET) -----
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# ----- Login Submit (POST) -----
@app.post("/login")
def login_user(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "admin123":
        response = JSONResponse(content={"success": True})
        response.set_cookie(key="logged_in", value="true", httponly=True)
        return response
    else:
        return JSONResponse(content={"success": False, "message": "Invalid username or password"})

# ----- Logout -----
@app.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    response = templates.TemplateResponse("logout.html", {"request": request})
    response.delete_cookie("logged_in")
    return response

# ----- Protected Home Page -----
@app.get("/home", response_class=HTMLResponse)
def home_page(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("home.html", {"request": request})

# ----- Protected Profile Page (HRD) -----
@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("profile.html", {"request": request})

# ----- Protected IAB Page -----
@app.get("/IAB", response_class=HTMLResponse)
def IAB_page(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("IAB.html", {"request": request})

# ================== GET OPERATOR + CERTIFICATION DATA ==================


# ----------------- API: OPERATOR (HRD) -------------
@app.get("/api/hrd/operator", response_class=JSONResponse)
def api_get_operator_hrd(nik: str, db: Session = Depends(get_db)):
    """
    Return operator basic data + photo (base64) + certification (latest) + form_status
    """
    op = crud.get_operator(db, nik)
    if not op:
        raise HTTPException(status_code=404, detail="Operator not found")

    photo_b64 = bytes_to_base64_str(op.photo)

    cert = crud.get_latest_certification(db, nik)
    cert_obj = None
    if cert:
        cert_obj = {
            "id": cert.id,
            "nik": cert.nik,
            "soldering_docno": cert.soldering_docno,
            "soldering_traindate": safe_date_to_iso(cert.soldering_traindate),
            "soldering_expdate": safe_date_to_iso(cert.soldering_expdate),

            "screwing_docno": cert.screwing_docno,
            "screwing_traindate": safe_date_to_iso(cert.screwing_traindate),
            "screwing_expdate": safe_date_to_iso(cert.screwing_expdate),

            "msa_docno": cert.msa_docno,
            "msa_traindate": safe_date_to_iso(cert.msa_traindate),
            "msa_expdate": safe_date_to_iso(cert.msa_expdate),

            "file_soldering": as_pdf_data_uri(cert.file_soldering),
            "file_screwing": as_pdf_data_uri(cert.file_screwing),
            "file_msa": as_pdf_data_uri(cert.file_msa),

            "status": cert.status,

            "soldering_written": cert.soldering_written,
            "soldering_practical": cert.soldering_practical,
            "soldering_result": cert.soldering_result,

            "screwing_technique": cert.screwing_technique,
            "screwing_work": cert.screwing_work,
            "screwing_result": cert.screwing_result,

            "ds_tiu": cert.ds_tiu,
            "ds_accu": cert.ds_accu,
            "ds_heco": cert.ds_heco,
            "ds_mcc": cert.ds_mcc,
            "ds_result": cert.ds_result,

            "process": cert.process,
            "ls_target": float(cert.ls_target) if cert.ls_target is not None else None,
            "ls_actual": float(cert.ls_actual) if cert.ls_actual is not None else None,
            "ls_achievement": float(cert.ls_achievement) if cert.ls_achievement is not None else None,
            "ls_result": cert.ls_result,

            "msaa_accuracy": cert.msaa_accuracy,
            "msaa_missrate": cert.msaa_missrate,
            "msaa_falsealarm": cert.msaa_falsealarm,
            "msaa_confidence": cert.msaa_confidence,
            "msaa_result": cert.msaa_result,
        }

    eval_doc = crud.get_latest_evaluation_document(db, nik)

    # Form status (logika lama dipertahankan)
    form_status = "Waiting"
    if eval_doc and eval_doc.op_train_eval and eval_doc.op_skills_eval and eval_doc.train_eval and eval_doc.eval_number:
        form_status = "Closed"
    elif cert_obj:
        form_status = "Closed"
    else:
        form_status = "New"

    return JSONResponse(content={
        "nik": op.nik,
        "name": op.name,
        "line": op.line,
        "job_level": op.level,  # frontend expects job_level
        "contract_status": op.contract_status,
        "end_contract_date": safe_date_to_iso(op.end_contract_date),
        "Photo": photo_b64,
        "form_status": form_status,
        "certification": cert_obj
    })

# -------------------- API: operator photo (binary) --------------------
@app.get("/api/operator/photo")
def api_get_photo(nik: str, db: Session = Depends(get_db)):
    op = crud.get_operator(db, nik)
    if not op or not op.photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return Response(content=op.photo, media_type="image/jpeg")

# -------------------- API: certification (by nik) - HRD (GET) --------------------
@app.get("/api/hrd/certification", response_class=JSONResponse)
def api_get_certification_hrd(nik: str, db: Session = Depends(get_db)):
    # gunakan kolom created_at yang benar (bukan CreatedAt)
    cert = (
        db.query(CertificationRecord)
        .filter(CertificationRecord.nik == nik)
        .order_by(CertificationRecord.created_at.desc())
        .first()
    )
    if not cert:
        raise HTTPException(status_code=404, detail="Certification record not found.")

    data = {
        "id": cert.id,
        "nik": cert.nik,
        "soldering_docno": cert.soldering_docno,
        "soldering_traindate": safe_date_to_iso(cert.soldering_traindate),
        "soldering_expdate": safe_date_to_iso(cert.soldering_expdate),  
        "screwing_docno": cert.screwing_docno,
        "screwing_traindate": safe_date_to_iso(cert.screwing_traindate),
        "screwing_expdate": safe_date_to_iso(cert.screwing_expdate),    
        "msa_docno": cert.msa_docno,
        "msa_traindate": safe_date_to_iso(cert.msa_traindate),
        "msa_expdate": safe_date_to_iso(cert.msa_expdate),  
      
        "file_soldering": cert.file_soldering,
        "file_screwing": cert.file_screwing,
        "file_msa": cert.file_msa,
        "status": cert.status,

        "soldering_written": cert.soldering_written,
        "soldering_practical": cert.soldering_practical,
        "soldering_result": cert.soldering_result,

        "screwing_technique": cert.screwing_technique,
        "screwing_work": cert.screwing_work,
        "screwing_result": cert.screwing_result,

        "ds_tiu": cert.ds_tiu,
        "ds_accu": cert.ds_accu,
        "ds_heco": cert.ds_heco,
        "ds_mcc": cert.ds_mcc,
        "ds_result": cert.ds_result,

        "process": cert.process,
        "ls_target": float(cert.ls_target) if cert.ls_target is not None else None,
        "ls_actual": float(cert.ls_actual) if cert.ls_actual is not None else None,
        "ls_achievement": float(cert.ls_achievement) if cert.ls_achievement is not None else None,
        "ls_result": cert.ls_result,

        "msaa_accuracy": cert.msaa_accuracy,
        "msaa_missrate": cert.msaa_missrate,
        "msaa_falsealarm": cert.msaa_falsealarm,
        "msaa_confidence": cert.msaa_confidence,
        "msaa_result": cert.msaa_result,
    }
    return JSONResponse(content=data)

# -------------------- API: create certification (schema) --------------------
@app.post("/api/certification")
def create_cert(data: CreateCertificationRecordSchema, db: Session = Depends(get_db)):
    try:
        payload = data.dict()
        print("📩 RAW Payload Received:", payload)

        result = crud.create_certification_record(db, payload)
        print("✅ Saved Certification Record")

        return {"message": "Certification saved successfully"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("❌ Error detail:", str(e))
        raise HTTPException(status_code=500, detail=str(e))








# -------------------- API: create certification - HRD (POST) --------------------
@app.post("/api/hrd/certification")
def create_certification_hrd(data:CreateCertificationRecordSchema, db: Session = Depends(get_db)):
    payload = data.dict()
    try:
        crud.create_certification_record(db, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Certification record created successfully"}

# -------------------- API: certification file upload - HRD --------------------
@app.post("/api/hrd/certification/upload")
def upload_certification_file_hrd(payload: dict = Body(...), db: Session = Depends(get_db)):
    """
    Frontend (profiles.js) mengirim payload seperti:
      - nik, status
      - salah satu set:
        * Soldering: soldering_docno, soldering_traindate, soldering_expdate, file_soldering
        * Screwing : screwing_docno,  screwing_traindate,  screwing_expdate,  file_screwing
        * MSA      : msa_docno,       msa_traindate,       msa_expdate,       file_msa
    Tidak ada field 'certification_type' dan 'file_base64'.
    Endpoint ini mendeteksi otomatis jenis sertifikat dari field file_* yang ada,
    lalu memanggil crud.update_certification_file_base64 agar tetap kompatibel
    dengan CRUD layer yang lama.
    """
    try:
        nik = payload["nik"]
    except KeyError:
        raise HTTPException(status_code=400, detail="Missing 'nik' in payload")

    # Deteksi jenis sertifikasi dari field file_*
    cert_type = None
    base64_str = None

    if "file_soldering" in payload and payload["file_soldering"]:
        cert_type = "Soldering"
        base64_str = payload["file_soldering"]
    elif "file_screwing" in payload and payload["file_screwing"]:
        cert_type = "Screwing"
        base64_str = payload["file_screwing"]
    elif "file_msa" in payload and payload["file_msa"]:
        cert_type = "MSA"
        base64_str = payload["file_msa"]

    if not cert_type or not base64_str:
        raise HTTPException(status_code=400, detail="No valid file_* field found in payload")

    try:
        crud.update_certification_file_base64(db, nik, cert_type, base64_str)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": f"{cert_type} file saved to database as base64"}

# -------------------- API: evaluation save (schema umum) --------------------
class EvaluationSaveIn(BaseModel):
    nik: str
    eval_number: str
    file_op_train_eval: str  # base64
    file_op_skills_eval: str  # base64
    file_train_eval: str  # base64
    upload_date: Optional[date] = Field(default_factory=lambda: datetime.utcnow().date())

    @validator("file_op_train_eval", "file_op_skills_eval", "file_train_eval")
    def validate_base64(cls, v):
        try:
            base64.b64decode(v)
        except Exception:
            raise ValueError("Invalid base64 file input")
        return v

# -------------------- API: evaluation save - HRD --------------------
@app.post("/api/hrd/evaluation/save")
def save_evaluation_document_hrd(data: EvaluationSaveIn, db: Session = Depends(get_db)):
    try:
        payload = data.dict()
        result = crud.save_evaluation_document(db, payload)
        return {"message": "Evaluation document saved successfully", "id": getattr(result, "id", None)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------- Simple health check --------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# ==============================
# ====== BAGIAN IAB PAGE =======
# ==============================

# API to get certification data by NIK (IAB_Page) - GET
@app.get("/api/iab/certification", response_class=JSONResponse)
def api_get_certification_iab(nik: str, db: Session = Depends(get_db)):
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
        "soldering_docno": cert.soldering_docno,
        "soldering_traindate": cert.soldering_traindate.isoformat() if cert.soldering_traindate else None,
        "soldering_expdate": cert.soldering_expdate.isoformat() if cert.soldering_expdate else None,
        "screwing_docno": cert.screwing_docno,
        "screwing_traindate": cert.screwing_traindate.isoformat() if cert.screwing_traindate else None,
        "screwing_expdate": cert.screwing_expdate.isoformat() if cert.screwing_expdate else None,
        "msa_docno": cert.msa_docno,
        "msa_traindate": cert.msa_traindate.isoformat() if cert.msa_traindate else None,
        "msa_expdate": cert.msa_expdate.isoformat() if cert.msa_expdate else None,

        "file_soldering": cert.file_soldering,
        "file_screwing": cert.file_screwing,
        "file_msa": cert.file_msa,
        "status": cert.status,

        "created_at": cert.created_at.isoformat() if cert.created_at else None,
    }

    return JSONResponse(content=data)

# API to update certification Document (IAB) - schema khusus untuk IAB (nama beda agar tidak bentrok)
class EvaluationSaveInIAB(BaseModel):
    nik: str
    eval_number: str
    file_op_train_eval: str  # base64
    file_op_skills_eval: str  # base64
    file_train_eval: str  # base64
    upload_date: date = Field(default_factory=lambda: datetime.utcnow().date())

    @validator("file_op_train_eval", "file_op_skills_eval", "file_train_eval")
    def validate_base64_iab(cls, v):
        try:
            base64.b64decode(v)
        except Exception:
            raise ValueError("Invalid base64 file input")
        return v

@app.post("/api/iab/evaluation/save")
def save_evaluation_document_iab(data: EvaluationSaveInIAB, db: Session = Depends(get_db)):
    try:
        print("Received raw data:", json.dumps(data.dict(), indent=2, default=str))
        payload = data.dict()
        result = crud.save_evaluation_document(db, payload)
        print("Saved document ID:", getattr(result, "id", None))
        return {"message": "Evaluation document saved successfully"}
    except Exception as e:
        print("Error when save evaluation document:", e)
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# ====== KOMPATIBILITAS: ROUTE LAMA TANPA PREFIX  =====
# (Dipertahankan agar tidak memutus frontend lama)
# =====================================================

# Versi lama: POST /certification (tanpa /api/hrd)
@app.post("/certification")
def create_cert_legacy(record_in: CreateCertificationRecordSchema, db: Session = Depends(get_db)):
    try:
        return crud.create_certification_record(db, record_in.dict())
    except Exception as e:
        print("Error saving certification:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")

# Versi lama: GET /api/certification (duplikat). Arahkan ke HRD GET terbaru.
@app.get("/api/certification", response_class=JSONResponse)
def api_get_certification_legacy(nik: str, db: Session = Depends(get_db)):
    return api_get_certification_hrd(nik=nik, db=db)

# Versi lama: POST /api/certification (duplikat). Arahkan ke HRD POST terbaru.
@app.post("/api/certification")
def create_certification_legacy(data: CreateCertificationRecordSchema, db: Session = Depends(get_db)):
    return create_certification_hrd(data=data, db=db)

# Versi lama: POST /api/certification/upload (duplikat). Arahkan ke HRD upload terbaru.
@app.post("/api/certification/upload")
def upload_certification_file_legacy(payload: dict = Body(...), db: Session = Depends(get_db)):
    return upload_certification_file_hrd(payload=payload, db=db)

# Versi lama: POST /api/evaluation/save (duplikat). Arahkan ke HRD save terbaru.
@app.post("/api/evaluation/save")
def save_evaluation_document_legacy(data: EvaluationSaveIn, db: Session = Depends(get_db)):
    return save_evaluation_document_hrd(data=data, db=db)
