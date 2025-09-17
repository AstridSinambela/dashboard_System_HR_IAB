from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi import UploadFile, File, Form, Body, Query
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from app.schemas import CreateCertificationRecordSchema, UpdateCertificationRecordSchema, CertificationRecordSchema
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from app import models, crud, database
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from app import models, crud, schemas
from .schemas import OperatorIABSchema, EvaluationDocumentSchema, SaveMergeIn, OperatorServerSideResponse
from app.models import TMOperator, CertificationRecord, EvaluationDocument, PDFOPT
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from io import BytesIO
from PyPDF2 import PdfMerger
import base64
import os
import shutil
import json
import traceback  
from starlette.middleware.sessions import SessionMiddleware
from .utils import verify_password


load_dotenv()
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Session Middleware (pakai SECRET_KEY dari .env)
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

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

def as_pdf_data_uri(possible_data):
    if not possible_data:
        return None
    s = str(possible_data).strip()
    # kalau sudah format data URI, langsung return
    if s.startswith("data:"):
        return s
    # kalau isinya panjang base64 tanpa prefix
    return f"data:application/pdf;base64,{s}"

def get_pdf_from_db(nama_file: str):
    try:
        with open(f"docs/{nama_file}", "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except:
        return None

# helper to read UploadFile and return base64 string
async def read_file_as_base64(upload_file: UploadFile) -> str:
    data = await upload_file.read()
    # optional: enforce file size limit on backend (e.g., 1MB)
    max_bytes = 1 * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File {upload_file.filename} too large (max 1MB).")
    # optional: check content-type
    if upload_file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail=f"File {upload_file.filename} must be a PDF.")
    return base64.b64encode(data).decode("utf-8")

# Dependency untuk ambil session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----- Helper: Check Login -----
def is_logged_in(request: Request):
    return request.session.get("logged_in") is True

def get_current_role(request: Request):
    return request.session.get("role_id")

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
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    # cari user berdasarkan email
    user = db.query(models.User).filter((models.User.email == username) | (models.User.name == username)).first()

    if not user or not verify_password(password, user.password):
        return JSONResponse(
            content={"success": False, "message": "Invalid username or password"}
        )

    # hanya role 2 (HR) dan 3 (IAB) yang bisa login
    if user.role_id not in [2, 3]:
        return JSONResponse(
            content={"success": False, "message": "Unauthorized role"}
        )

    # simpan session
    request.session["logged_in"] = True
    request.session["user_id"] = user.id
    request.session["role_id"] = user.role_id

    return JSONResponse(content={"success": True})

# ----- Logout -----
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")

# ----- Protected Home Page -----
@app.get("/home", response_class=HTMLResponse)
def home_page(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/login")

    role_id = get_current_role(request)
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "role_id": role_id},
    )

# ----- Protected Profile Page (HRD) -----
@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/login")

    if get_current_role(request) != 2:
        raise HTTPException(status_code=403, detail="Access forbidden for this role")

    return templates.TemplateResponse("profile.html", {"request": request})

# ----- Protected IAB Page -----
# ---- IAB Page (role 3 only)
@app.get("/IAB", response_class=HTMLResponse)
def IAB_page(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/login")

    if get_current_role(request) != 3:
        raise HTTPException(status_code=403, detail="Access forbidden for this role")

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
    if eval_doc and eval_doc.op_train_eval and eval_doc.op_skills_eval and eval_doc.train_eval:
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
      
        "file_soldering":  as_pdf_data_uri(cert.file_soldering),
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
    try:
        nik = payload["nik"]
    except KeyError:
        raise HTTPException(status_code=400, detail="Missing 'nik' in payload")

    cert_type = None
    base64_str = None
    docno, traindate, expdate = None, None, None

    if "file_soldering" in payload and payload["file_soldering"]:
        cert_type = "Soldering"
        base64_str = payload["file_soldering"]
        docno = payload.get("soldering_docno")
        traindate = payload.get("soldering_traindate")
        expdate = payload.get("soldering_expdate")

    elif "file_screwing" in payload and payload["file_screwing"]:
        cert_type = "Screwing"
        base64_str = payload["file_screwing"]
        docno = payload.get("screwing_docno")
        traindate = payload.get("screwing_traindate")
        expdate = payload.get("screwing_expdate")

    elif "file_msa" in payload and payload["file_msa"]:
        cert_type = "MSA"
        base64_str = payload["file_msa"]
        docno = payload.get("msa_docno")
        traindate = payload.get("msa_traindate")
        expdate = payload.get("msa_expdate")

    if not cert_type or not base64_str:
        raise HTTPException(status_code=400, detail="No valid file_* field found in payload")

    try:
        crud.update_certification_file_base64(
            db, nik, cert_type, base64_str,
            docno=docno,
            traindate=traindate,
            expdate=expdate,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": f"{cert_type} file saved to database as base64"}


# -------------------- API: view PDF from base64 in DB --------------------
@app.get("/view-pdf/{file_name}")
def view_pdf(file_name: str):
    file_data = get_pdf_from_db(file_name)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")

    # decode dari base64 → bytes
    pdf_bytes = base64.b64decode(file_data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{file_name}"'
        }
    )

# -------------------- API: evaluation save (schema umum) --------------------
class EvaluationSaveIn(BaseModel):
    nik: str
    op_train_eval: str  # base64
    op_skills_eval: str  # base64
    train_eval: str  # base64
    upload_date: Optional[date] = Field(default_factory=lambda: datetime.utcnow().date())

    @validator("op_train_eval", "op_skills_eval", "train_eval")
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

# ==============================
# ====== BAGIAN IAB PAGE =======
# ==============================

# ----------------- API: list operators (NIK + Name) -----------------
@app.get("/api/operators", response_model=OperatorServerSideResponse)
def get_operators_server_side(
   search: str = Query("", description="Search keyword"),
    start: int = Query(0, ge=0),
    length: int = Query(10, ge=1),
    order_col: int = Query(0, ge=0),
    order_dir: str = Query("asc"),
    db: Session = Depends(get_db)
):
    total, filtered, items = crud.get_operators(
        db, search=search, start=start, length=length,
        order_col=order_col, order_dir=order_dir
    )

    return {
        "recordsTotal": total,       # total semua data
        "recordsFiltered": filtered, # hasil filter
        "data": items
    }

    
# API to get operator data (IAB_Page)
@app.get("/api/operator/iab")
def api_get_operator_iab(nik: Optional[str] = None, db: Session = Depends(get_db)):
    if not nik:
        raise HTTPException(status_code=400, detail="NIK is required")

    op = crud.get_operator(db, nik)
    if not op:
        raise HTTPException(status_code=404, detail="Operator not found")

    # Certification
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

    # Evaluation Document
    eval_doc = crud.get_latest_evaluation_document(db, nik)
    eval_data = None  
    if eval_doc:
        eval_data = {
            "op_train_eval": as_pdf_data_uri(eval_doc.op_train_eval) if eval_doc.op_train_eval else None,
            "op_skills_eval": as_pdf_data_uri(eval_doc.op_skills_eval) if eval_doc.op_skills_eval else None,
            "train_eval": as_pdf_data_uri(eval_doc.train_eval)  if eval_doc.train_eval else None,
            "upload_date": eval_doc.upload_date.isoformat() if eval_doc.upload_date else None,
        }

    if eval_data:
        form_status = "Closed"
    elif cert_obj:
        form_status = "New"
    else:
        form_status = "Waiting"

    file_base64 = eval_data.get("op_train_eval") if eval_data else None
    photo_b64 = bytes_to_base64_str(op.photo)

    return {
        "nik": op.nik,
        "name": op.name,
        "line": op.line,
        "contract_status": op.contract_status,
        "end_contract_date": op.end_contract_date.isoformat() if op.end_contract_date else None,
        "job_level": op.level,
        "Photo": photo_b64,
        "certification": cert_obj,
        "evaluation": eval_data,
        "form_status": form_status,
        "file_base64": file_base64
    }



# API to get certification data by NIK (IAB_Page)
@app.get("/api/certification", response_class=JSONResponse)
def api_get_certification(nik: str, db: Session = Depends(get_db)):
    cert = (db.query(models.CertificationRecord)
        .filter(models.CertificationRecord.nik == nik)
        .order_by(models.CertificationRecord.created_at.desc())
        .first()
    )
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
        "soldering_traindate": safe_date_to_iso(cert.soldering_traindate),
        "soldering_expdate": safe_date_to_iso(cert.soldering_expdate),  
        "file_soldering": as_pdf_data_uri(cert.file_soldering),
        
        "screwing_docno": cert.screwing_docno,
        "screwing_traindate": safe_date_to_iso(cert.screwing_traindate),
        "screwing_expdate": safe_date_to_iso(cert.screwing_expdate),    
        "file_screwing":  as_pdf_data_uri(cert.file_screwing),

        "msa_docno": cert.msa_docno,
        "msa_traindate": safe_date_to_iso(cert.msa_traindate),
        "msa_expdate": safe_date_to_iso(cert.msa_expdate),  
        "file_msa": as_pdf_data_uri(cert.file_msa),
        "status": cert.status,
    }

    return JSONResponse(content=data)


@app.get("/api/evaluation", response_model=EvaluationDocumentSchema | None)
def get_evaluation_document(nik: str, db: Session = Depends(get_db)):
    record = (
        db.query(EvaluationDocument)
        .filter(EvaluationDocument.nik == nik)
        .order_by(EvaluationDocument.upload_date.desc())
        .first()
    )
    if not record:
        return Response(status_code=204)  # Biar frontend tahu kosong
    return record

@app.post("/api/savemerge")
def save_merge(data: SaveMergeIn, db: Session = Depends(get_db)):
    try:
        print("📩 Payload diterima:", data.dict())  # debug isi body
        result = crud.save_evaluation_and_merge(db, data.dict())
        return {"message": "Evaluation data saved successfully", "data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Save+Merge failed: {str(e)}")
