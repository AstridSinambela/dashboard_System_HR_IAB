from datetime import datetime
import os
import io
from typing import Optional, List
from fastapi import FastAPI, Request, Depends, Form, Response, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from app import websocket_manager
from app.auth_dependencies import role_required, current_user
from dotenv import load_dotenv
from . import database, models, crud
from . import utils

load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))
# DB
models.Base.metadata.create_all(bind=database.engine)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

#static folder (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

#websocket

@app.websocket("/ws/cos")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            # tunggu event dari client (optional, biar gak block lama)
            data = await websocket.receive_text()
            print("📩 message dari client:", data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

#---------------------------
#Build File Data Operator
#---------------------------

# ----------------------------
# Login Section
# ----------------------------
@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "msg": ""})

@app.post("/login", response_class=HTMLResponse)
def login_user(
    request: Request,
    response: Response,
    identifier: str = Form(...), 
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        (models.User.name == identifier) | (models.User.email == identifier)
    ).first()

    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "msg": "User not found"})

    if not utils.verify_password(password, user.password):
        return templates.TemplateResponse("login.html", {"request": request, "msg": "Invalid password"})

    # Set session
    request.session["user_id"] = user.id
    request.session["role_id"] = user.role_id

    # Redirect berdasarkan role_id
    if user.role_id == 1:
        return RedirectResponse(url="/index", status_code=303)
    elif user.role_id == 2:
        return RedirectResponse(url="/hr/index_hr", status_code=303)
    elif user.role_id == 3:
        return RedirectResponse(url="/iab_staff/index_iabs", status_code=303)
    elif user.role_id == 4:
        return RedirectResponse(url="/issuer/index_is", status_code=303)
    elif user.role_id == 5:
        return RedirectResponse(url="/checker/index_ch", status_code=303)
    elif user.role_id == 6:
        return RedirectResponse(url="/pdm/index_pdm", status_code=303)
    elif user.role_id == 7:
        return RedirectResponse(url="/qach/index_qach", status_code=303)
    elif user.role_id == 8:
        return RedirectResponse(url="/qaapv/index_qaapv", status_code=303)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "msg": "Role not recognized"})

@app.get("/logout")
async def logout(request: Request):
    # hapus session user
    request.session.clear()
    # redirect ke halaman login (atau root "/")
    return RedirectResponse(url="/", status_code=303)

    
#------------
# Main Page
#------------

@app.get("/index", response_class=HTMLResponse)
def home(request: Request, _: None = role_required([1])):  # hanya admin
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/navbar", response_class=HTMLResponse)
async def get_navbar(request: Request):
    return templates.TemplateResponse("navbar.html", {"request": request})

@app.get("/content", response_class=HTMLResponse)
async def get_content(request: Request):
    return templates.TemplateResponse("content.html", {"request": request})

@app.get("/footer", response_class=HTMLResponse)
async def get_footer(request: Request):
    return templates.TemplateResponse("footer.html", {"request": request})

# User management
@app.get("/data_user", response_class=HTMLResponse)
async def get_data_user(request: Request, db: Session = Depends(get_db)):
    users = crud.get_users(db)
    return templates.TemplateResponse("data_user.html", {"request": request, "users": users})

@app.get("/edit_user/{user_id}", response_class=HTMLResponse)
async def edit_user_form(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    return templates.TemplateResponse("edit_user.html", {"request": request, "user": user})

@app.post("/create_user")
async def create_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    firstname: str = Form(""),
    lastname: str = Form(""),
    gender: int = Form(0),
    role_id: int = Form(2),
    db: Session = Depends(get_db),
):
    fullname = f"{firstname} {lastname}".strip()
    user_data = {
        "name": name,
        "email": email,
        "password": utils.hash_password(password),
        "firstname": firstname,
        "lastname": lastname,
        "fullname": fullname,
        "gender": gender,
        "role_id": role_id,
    }
    crud.create_user(db, user_data)
    return RedirectResponse(url="/data_user", status_code=303)

@app.post("/delete_user/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    crud.delete_user(db, user_id)
    return RedirectResponse(url="/data_user", status_code=303)

@app.post("/edit_user/{user_id}")
async def edit_user(
    user_id: int,
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(""),
    firstname: str = Form(""),
    lastname: str = Form(""),
    gender: int = Form(0),
    role_id: int = Form(2),
    db: Session = Depends(get_db),
):
    fullname = f"{firstname} {lastname}".strip()
    update_data = {
        "name": name,
        "email": email,
        "firstname": firstname,
        "lastname": lastname,
        "fullname": fullname,
        "gender": gender,
        "role_id": role_id,
    }

    if password:
        update_data["password"] = utils.hash_password(password)

    crud.update_user(db, user_id, update_data)
    return RedirectResponse(url="/data_user", status_code=303)


# ----------------------------
# ROUTE untuk Issuer
# ----------------------------
@app.get("/issuer/index_is", response_class=HTMLResponse)
async def issuer_home(request: Request, _: None = role_required([1, 4, 5])): 
    return templates.TemplateResponse("issuer/index_is.html", {"request": request})

@app.get("/issuer/content", response_class=HTMLResponse)
async def issuer_content(request: Request, _: None = role_required([1, 4, 5])):  
    return templates.TemplateResponse("issuer/content.html", {"request": request})

@app.get("/issuer/navbar", response_class=HTMLResponse)
async def issuer_navbar(request: Request, _: None = role_required([1, 4, 5])):  
    return templates.TemplateResponse("issuer/navbar.html", {"request": request})

@app.get("/issuer/data_cos")
def read_data_cos(request: Request, db: Session = Depends(get_db), _: None = role_required([1, 4, 5])):
    cos_list = crud.get_all_document_groups(db)
    id_cos_list = [row[0].id_cos for row in cos_list]  # Ambil id_cos dari objek DocumentGroup di tuple
    return templates.TemplateResponse("issuer/data_cos.html", {
        "request": request,
        "cos_list": cos_list,
        "id_cos_list": id_cos_list
    })

@app.get("/issuer/add_cos")
def add_cos_form(
    request: Request,
    id_cos: Optional[str] = None,
    db: Session = Depends(get_db),
    _: None = role_required([1, 4, 5])
):
    operators = crud.get_all_pdfopt(db)
    operators_list = [
        {
            "id": op.id,
            "nik": op.nik,
            "name": op.name,
            "pdf_path": f"operator_file_{op.name}_{op.nik}.pdf"
        }
        for op in operators
    ]
    return templates.TemplateResponse("issuer/add_cos.html", {
        "request": request,
        "operators": operators_list,
        "id_cos": id_cos
    })


@app.post("/issuer/add_cos")
async def add_cos(
    request: Request,
    id_cos: str = Form(...),
    operator_ids: Optional[List[int]] = Form(default=[], alias="operator_ids[]"),
    db: Session = Depends(get_db),
    _: None = role_required([1, 4, 5])
):
    user_id = request.session.get("user_id")  # 🔥 ambil user yang login
    cos = crud.get_document_group_by_id(db, id_cos)

    if cos:
        # update → kasih updated_by
        if operator_ids:
            crud.add_operator_to_group(db, id_cos=id_cos, operator_ids=operator_ids)
            crud.update_document_group(db, id_cos, {"status": 2}, user_id=user_id)
    else:
        # create → created_by & updated_by = user_id
        status = 1
        if operator_ids:
            status = 2
        new_cos = crud.create_document_group(db, id_cos=id_cos, status=status, user_id=user_id)
        
        if operator_ids:
            crud.add_operator_to_group(db, id_cos=id_cos, operator_ids=operator_ids)
        
        total_opt = (
            db.query(func.count(models.GroupOperator.id))
            .filter(models.GroupOperator.id_cos == new_cos.id_cos)
            .scalar()
        )

        # 🔥 Ambil nama user
        creator = db.query(models.User).filter(models.User.id == new_cos.created_by).first()
        updater = db.query(models.User).filter(models.User.id == new_cos.updated_by).first()
        creator_name = (creator.firstname or creator.fullname or creator.name if creator else "-")
        updater_name = (updater.firstname or updater.fullname or updater.name if updater else "-")
        status_map = {
            1: "New",
            2: "Waiting Upload Evaluation",
            3: "Complete - Waiting Ready to Circulation",
            4: "Complete - Waiting Approve",
            5: "Done"
        }

        await websocket_manager.broadcast({
            "event": "new_cos",
            "id_cos": new_cos.id_cos,
            "status": status_map.get(new_cos.status, "Unknown"),
            "created_at": new_cos.created_at.isoformat(),
            "updated_at": new_cos.updated_at.isoformat() if new_cos.updated_at else None,
            "creator_name": creator_name,
            "updater_name": updater_name,
            "total_opt": total_opt
        })
        

    return RedirectResponse(url=f"/issuer/detail_cos?id_cos={id_cos}", status_code=303)


@app.get("/issuer/detail_cos", response_class=HTMLResponse)
def detail_cos(id_cos: str, request: Request, db: Session = Depends(get_db), _: None = role_required([1, 4, 5])):
    cos = crud.get_document_group_by_id(db, id_cos=id_cos)
    if not cos:
        raise HTTPException(status_code=404, detail="Document Group not found")
    
    operators = crud.get_operators_by_cos(db, id_cos=id_cos)
    documents = crud.get_documents_for_group(db, id_cos=id_cos)

    required_docs = {"COS", "PFM", "WGS", "MO"}
    uploaded_types = {doc.doc_type for doc in documents}
    missing_docs = required_docs - uploaded_types

    already_circulated = crud.is_cos_already_circulated(db, id_cos)

    return templates.TemplateResponse("issuer/detail_cos.html", {
        "request": request,
        "cos": cos,
        "operators": operators,
        "documents": documents,
        "missing_docs": missing_docs,
        "already_circulated": already_circulated
    })


from fastapi import APIRouter  
router = APIRouter()
@router.get("/issuer/file/{id_cos}/{doc_id}")
def get_file(id_cos: str, doc_id: int, db: Session = Depends(get_db)):
    from urllib.parse import unquote
    decoded_id_cos = unquote(id_cos)

    doc = (
        db.query(models.DocumentForGroup)
        .filter(models.DocumentForGroup.id_cos == decoded_id_cos, models.DocumentForGroup.id == doc_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document not found for {decoded_id_cos}")

    # 🔑 ambil mime_type dari DB
    mime_type = doc.mime_type or "application/octet-stream"

    return StreamingResponse(
        io.BytesIO(doc.file_content),
        media_type=mime_type,
        headers={"Content-Disposition": f'inline; filename="{doc.file_name}"'}
    )

@app.get("/issuer/eval_report", response_class=HTMLResponse)
async def eval_report(
    request: Request,
    db: Session = Depends(get_db),
    _: None = role_required([1, 4, 5])
):
    cos_list = crud.get_cos_for_eval_report(db)
    id_cos_list = [cos.id_cos for cos in cos_list]

    return templates.TemplateResponse("issuer/eval_report.html", {
        "request": request,
        "id_cos_list": id_cos_list,
        "documents": []  # default kosong, akan diisi setelah pilih COS
    })

@app.get("/issuer/eval_report/{id_cos:path}", response_class=HTMLResponse)
async def eval_report_cos(
    id_cos: str,
    request: Request,
    db: Session = Depends(get_db),
    _: None = role_required([1, 4, 5 ])
):
    from urllib.parse import unquote
    decoded_id_cos = unquote(id_cos)  # decode %20, %28, %29, %2F dll

    cos_list = crud.get_cos_for_eval_report(db)
    id_cos_list = [cos.id_cos for cos in cos_list]

    documents = crud.get_documents_for_group(db, id_cos=decoded_id_cos)

    return templates.TemplateResponse("issuer/eval_report.html", {
        "request": request,
        "id_cos_list": id_cos_list,
        "selected_cos": decoded_id_cos,
        "documents": documents
    })



@app.post("/issuer/eval_report")
async def upload_eval_report(
    request: Request,
    id_cos: str = Form(...),
    change_order_sheet: Optional[UploadFile] = File(None),
    process_flex_matrix: Optional[UploadFile] = File(None),
    wgs_file: Optional[UploadFile] = File(None),
    mo_file: Optional[UploadFile] = File(None),
    others_file: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    _: None = role_required([1, 4, 5])
):
    user_id = request.session.get("user_id")
    # 3 file utama
    files = {
        "COS": change_order_sheet,
        "PFM": process_flex_matrix,
        "WGS": wgs_file,
        "MO": mo_file,
    }
    for doc_type, file in files.items():
        if file and file.filename:
            content = await file.read()
            mime_type = file.content_type
            crud.upsert_document(db, id_cos, doc_type, file.filename, content, user_id=user_id, mime_type=mime_type)

    # Others (multiple)
    if others_file:
        for file in others_file:
            if file and file.filename:
                content = await file.read()
                mime_type = file.content_type
                crud.upsert_document(db, id_cos, "OTHERS", file.filename, content, user_id=user_id, mime_type=mime_type)

    # Update status group
    crud.update_document_group_status(db, id_cos)

    # 🔥 Generate final PDF otomatis
    from .pdf_generator import generate_final_pdf
    generate_final_pdf(db, id_cos)

    return RedirectResponse(url=f"/issuer/detail_cos?id_cos={id_cos}", status_code=303)

@router.get("/issuer/operator_file/{file_name}")
def get_operator_file(file_name: str, db: Session = Depends(get_db)):
    """
    file_name contoh: "2_operator_file_18062061.pdf"
    """
    # Ambil id dari bagian awal nama file
    try:
        pdf_id = int(file_name.split("_")[0])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file format")

    # Cari record PDFOPT
    doc = db.query(models.PDFOPT).filter(models.PDFOPT.id == pdf_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Operator file not found")

    # Decode PDF dari base64
    try:
        pdf_bytes = base64.b64decode(doc.merged_pdf)
    except Exception:
        raise HTTPException(status_code=500, detail="Invalid base64 PDF data")

    # Nama file download → pakai id + nik
    download_name = f"{doc.id}_operator_file_({doc.nik}).pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="apllication/pdf",
        headers={"Content-Disposition": f'inline; filename="{download_name}"'}
    )

@router.get("/issuer/final_pdf/{id_cos}")
def get_final_pdf(id_cos: str, db: Session = Depends(get_db)):
    final = (
        db.query(models.PDFGroupFinal)
        .filter(models.PDFGroupFinal.id_cos == id_cos)
        .order_by(models.PDFGroupFinal.generated_at.desc())
        .first()
    )
    if not final:
        raise HTTPException(status_code=404, detail="Final PDF not found")

    return StreamingResponse(
        io.BytesIO(final.final_pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="final_{id_cos}.pdf"'}
    )



@app.get("/issuer/eval_circulate", response_class=HTMLResponse)
async def eval_circulate(request: Request, db: Session = Depends(get_db), _: None = role_required([1, 4, 5])):  
    data = crud.get_eval_circulate_data(db)
    return templates.TemplateResponse("issuer/eval_circulate.html", {
        "request": request,
        "documents": data
    })

@app.get("/issuer/add_circulate")
def add_circulate(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(current_user),
    id_cos: str | None = None,   # 🔹 tangkap id_cos dari query
    _: None = role_required([1, 4, 5])
):
    ready_docs = crud.get_available_cos_for_evaluation(db)

    users_checked = crud.get_users_by_roles(db, [5, 6])
    users_approved = crud.get_users_by_roles(db, [6])
    users_qa_checked = crud.get_users_by_roles(db, [7, 8])
    users_qa_approved = crud.get_users_by_roles(db, [8])

    return templates.TemplateResponse("issuer/add_circulate.html", {
        "request": request,
        "docs": ready_docs,
        "issuer": user,
        "id_cos": id_cos,   # 🔹 lempar ke template
        "users_checked": users_checked,
        "users_approved": users_approved,
        "users_qa_checked": users_qa_checked,
        "users_qa_approved": users_qa_approved
    })


@app.post("/issuer/add_circulate")
async def save_circulate(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(current_user)
):
    form = await request.form()
    id_cos = form.get("id_cos")

    task_assignments = {
        "CHECK": form.get("checked_id"),
        "APPROVE": form.get("approved_id"),
        "QA_CHECK": form.get("qa_checked_id"),
        "QA_APPROVE": form.get("qa_approved_id")
    }

    eval_group = crud.create_evaluation_with_tasks(db, id_cos, user.id, task_assignments)
    if not eval_group:
        raise HTTPException(status_code=400, detail="Invalid COS / PDFFinal not found")

    
    # 2️⃣ update status DocumentGroup → 4 (Complete - Waiting approve circulate)
    crud.update_document_group(db, id_cos, {"status": 4}, user_id=user.id)

    return RedirectResponse(url="/issuer/eval_circulate", status_code=303)

@app.get("/issuer/detail_circulate", response_class=HTMLResponse)
def detail_circulate(id_cos: str, request: Request, db: Session = Depends(get_db), _: None = role_required([1,4,5])):
    data = crud.get_detail_circulate(db, id_cos)
    if not data:
        raise HTTPException(status_code=404, detail="Circulate not found")

    # mapping status
    status_map = {
        1: "New",
        2: "Waiting Checker",
        3: "Need Revision from Checker",
        4: "Waiting Approval",
        5: "Need Revision from Approver",
        6: "Waiting QA Check",
        7: "Need Revision from QA Check",
        8: "Waiting QA Approval",
        9: "Need Revision from QA Approval",
        10: "Completed"
    }

    return templates.TemplateResponse("issuer/detail_circulate.html", {
        "request": request,
        "cos": data,
        "status_text": status_map.get(data["status"], "Unknown")
    })


# Several Role
@app.get("/eval_assigned", response_class=HTMLResponse)
async def issuer_eval_assigned(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(current_user)
):
    assigned = crud.get_assigned_evaluations(db, user.id)  # ✅ hanya dari EvalTask
    return templates.TemplateResponse(
        "eval_assigned.html",
        {"request": request, "assigned": assigned}
    )

@app.get("/check_evaluation", response_class=HTMLResponse)
def check_evaluation(
    request: Request,
    id_cos: str,
    db: Session = Depends(get_db),
    user=Depends(current_user)
):
    detail = crud.get_detail_circulate(db, id_cos)
    if not detail:
        raise HTTPException(status_code=404, detail="COS not found")

    revisions = crud.get_revisions_by_cos(db, id_cos)

    users = (
        db.query(models.User)
        .filter(models.User.role_id.in_([4, 5]))
        .all()
    )

    # mapping status
    status_map = {
        1: "New",
        2: "Waiting Checker",
        3: "Need Revision from Checker",
        4: "Waiting Approval",
        5: "Need Revision from Approver",
        6: "Waiting QA Check",
        7: "Need Revision from QA Check",
        8: "Waiting QA Approval",
        9: "Need Revision from QA Approval",
        10: "Completed"
    }

    return templates.TemplateResponse(
        "check_evaluation.html",
        {
            "request": request,
            "cos": detail,
            "revisions": revisions,
            "users": users,
            "user": user,
            "status_text": status_map.get(detail["status"], "Unknown")
        },
    )

@app.post("/check_evaluation/add_revision")
async def add_revision(
    request: Request,
    id_cos: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    content = await file.read()
    crud.create_revision(
        db=db,
        id_cos=id_cos,
        description=description,
        file_name=file.filename,
        file_content=content,
        mime_type=file.content_type,
        created_by=user.id,
    )
    return RedirectResponse(url=f"/check_evaluation?id_cos={id_cos}", status_code=303)


@router.get("/revision_file/{rev_id}")
def get_revision_file(rev_id: int, db: Session = Depends(get_db)):
    rev = db.query(models.EvalRevision).filter(models.EvalRevision.id == rev_id).first()
    if not rev or not rev.file_content:
        raise HTTPException(status_code=404, detail="Revision file not found")

    return StreamingResponse(
        io.BytesIO(rev.file_content),
        media_type=rev.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{rev.file_name}"'}
    )

#--------------
#Pr Manager
#--------------
@app.get("/pdm/index_pdm", response_class=HTMLResponse)
async def hr_home(request: Request, _: None = role_required([1, 6])): 
    return templates.TemplateResponse("pdm/index_pdm.html", {"request": request})


@app.get("/pdm/content", response_class=HTMLResponse)
async def get_content(request: Request):
    return templates.TemplateResponse("/pdm/content.html", {"request": request})

@app.get("/pdm/navbar", response_class=HTMLResponse)
async def hr_navbar(request: Request, _: None = role_required([1, 6])):  
    return templates.TemplateResponse("pdm/navbar.html", {"request": request})

#--------------
# HR Route
#--------------
@app.get("/hr/index_hr", response_class=HTMLResponse)
async def hr_home(request: Request, _: None = role_required([1, 2])): 
    return templates.TemplateResponse("hr/index_hr.html", {"request": request})

@app.get("/hr/content", response_class=HTMLResponse)
async def hr_content(request: Request, _: None = role_required([1, 2])):  
    return templates.TemplateResponse("hr/content.html", {"request": request})

@app.get("/hr/navbar", response_class=HTMLResponse)
async def hr_navbar(request: Request, _: None = role_required([1, 2])):  
    return templates.TemplateResponse("hr/navbar.html", {"request": request})


#--------------
#Chekcer Route
#--------------
@app.get("/checker/index_ch", response_class=HTMLResponse)
async def checker_home(request: Request, _: None = role_required([1, 5])): 
    return templates.TemplateResponse("checker/index_ch.html", {"request": request})

@app.get("/checker/content", response_class=HTMLResponse)
async def checker_content(request: Request, _: None = role_required([1, 5])):  
    return templates.TemplateResponse("checker/content.html", {"request": request})

@app.get("/checker/navbar", response_class=HTMLResponse)
async def checker_navbar(request: Request, _: None = role_required([1, 5])):  
    return templates.TemplateResponse("checker/navbar.html", {"request": request})


#--------------
#QA Route
#--------------
@app.get("/qa/index_qa", response_class=HTMLResponse)
async def qa_home(request: Request, _: None = role_required([1, 6])): 
    return templates.TemplateResponse("qa/index_qa.html", {"request": request})

@app.get("/qa/content", response_class=HTMLResponse)
async def qa_content(request: Request, _: None = role_required([1, 6])):  
    return templates.TemplateResponse("qa/content.html", {"request": request})

@app.get("/qa/navbar", response_class=HTMLResponse)
async def qa_navbar(request: Request, _: None = role_required([1, 6])):  
    return templates.TemplateResponse("qa/navbar.html", {"request": request})


#-------------
#IAB_STAFF Route
#-------------
@app.get("/iab_staff/index_iabs", response_class=HTMLResponse)
async def iab_staff_home(request: Request, _: None = role_required([1, 3])): 
    return templates.TemplateResponse("iab_staff/index_iabs.html", {"request": request})

@app.get("/iab_staff/content", response_class=HTMLResponse)
async def iab_staff_content(request: Request, _: None = role_required([1, 3])):  
    return templates.TemplateResponse("iab_staff/content.html", {"request": request})

@app.get("/iab_staff/navbar", response_class=HTMLResponse)
async def iab_staff_navbar(request: Request, _: None = role_required([1, 3])):  
    return templates.TemplateResponse("iab_staff/navbar.html", {"request": request})


@app.get("/test_show_pdf", response_class=HTMLResponse)
async def test_show_pdf(request: Request):  
    return templates.TemplateResponse("test_show_pdf.html", {"request": request})

import base64
@app.get("/get_pdf/{nik}")
async def get_pdf(nik: str, db: Session = Depends(get_db)):
    pdf_record = db.query(models.PDFOPT).filter(models.PDFOPT.nik == nik).first()
    if not pdf_record:
        return {"error": "PDF not found"}

    base64_str = pdf_record.merged_pdf
    try:
        pdf_bytes = base64.b64decode(base64_str)
    except Exception as e:
        return {"error": f"Failed to decode PDF: {e}"}

    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf")

app.include_router(router)