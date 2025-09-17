import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, literal
from . import models
from . import models

def create_user(db: Session, user_data: dict):
    user = models.User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.User)
        .order_by(models.User.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def update_user(db: Session, user_id: int, update_data: dict):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    for key, value in update_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user

def create_pdf_record(db: Session, nik: str, pdf_path: str):
    new_pdf = models.GeneratedPDFOperator(
        nik=nik,
        pdf_path=pdf_path
    )
    db.add(new_pdf)
    db.commit()
    db.refresh(new_pdf)
    return new_pdf



def create_document_group(db: Session, id_cos: str, status: int = 1, user_id: int = None):
    new_cos = models.DocumentGroup(
        id_cos=id_cos,
        status=status,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=user_id,
        updated_by=user_id
    )
    db.add(new_cos)
    db.commit()
    db.refresh(new_cos)
    return new_cos


def add_operator_to_group(db: Session, id_cos: str, operator_ids: list[int]):
    for op_id in operator_ids:
        new_group_op = models.GroupOperator(
            id_cos=id_cos,
            pdf_operator_id=op_id,
            created_at=datetime.utcnow()
        )
        db.add(new_group_op)
    db.commit()

def get_all_pdfopt(db: Session):
    return (
        db.query(
            models.PDFOPT.id.label("id"),
            models.PDFOPT.nik.label("nik"),
            models.TMOperator.name.label("name")
        )
        .join(models.TMOperator, models.PDFOPT.nik == models.TMOperator.nik, isouter=True)
        .all()
    )


from sqlalchemy.orm import aliased

def get_all_document_groups(db: Session):
    created_user = aliased(models.User)
    updated_user = aliased(models.User)

    results = (
        db.query(
            models.DocumentGroup,
            func.count(models.GroupOperator.id).label("total_opt"),
            created_user.firstname.label("creator_name"),
            updated_user.firstname.label("updater_name"),
        )
        .outerjoin(models.GroupOperator, models.DocumentGroup.id_cos == models.GroupOperator.id_cos)
        .outerjoin(created_user, created_user.id == models.DocumentGroup.created_by)
        .outerjoin(updated_user, updated_user.id == models.DocumentGroup.updated_by)
        .group_by(
            models.DocumentGroup.id_cos,
            models.DocumentGroup.created_at,
            models.DocumentGroup.updated_at,
            models.DocumentGroup.status,
            models.DocumentGroup.created_by,
            models.DocumentGroup.updated_by,
            created_user.firstname,
            updated_user.firstname,
        )
        .order_by(models.DocumentGroup.created_at.desc())
        .all()
    )
    return results


def get_document_group_by_id(db: Session, id_cos: str):
    return db.query(models.DocumentGroup).filter(models.DocumentGroup.id_cos == id_cos).first()

def get_operators_by_cos(db: Session, id_cos: str):
    results = (
        db.query(
            models.TMOperator.nik,
            models.TMOperator.name,
            models.PDFOPT.id.label("pdf_id")
        )
        .join(models.PDFOPT, models.TMOperator.nik == models.PDFOPT.nik)
        .join(models.GroupOperator, models.GroupOperator.pdf_operator_id == models.PDFOPT.id)
        .filter(models.GroupOperator.id_cos == id_cos)
        .all()
    )

    # Format filename sama dengan add_cos.html
    return [
        (
            r.nik,
            r.name,
            r.pdf_id,
            f"operator_file_{r.name}_{r.nik}.pdf"
        )
        for r in results
    ]





def get_documents_for_group(db: Session, id_cos: str):
    """
    Ambil semua dokumen dari T_DocumentForGroup berdasarkan id_cos
    """
    return (
        db.query(models.DocumentForGroup)
        .filter(models.DocumentForGroup.id_cos == id_cos)
        .order_by(models.DocumentForGroup.uploaded_at.desc())
        .all()
    )


def get_cos_for_eval_report(db: Session):
    return (
        db.query(models.DocumentGroup.id_cos, models.DocumentGroup.created_at)
        .join(models.GroupOperator, models.GroupOperator.id_cos == models.DocumentGroup.id_cos)
        .filter(models.DocumentGroup.status == 2)
        .group_by(models.DocumentGroup.id_cos, models.DocumentGroup.created_at)
        .order_by(models.DocumentGroup.created_at.desc())
        .all()
    )

def update_document_group(db: Session, id_cos: str, update_data: dict, user_id: int = None):
    cos = db.query(models.DocumentGroup).filter(models.DocumentGroup.id_cos == id_cos).first()
    if not cos:
        return None
    for key, value in update_data.items():
        setattr(cos, key, value)
    cos.updated_at = datetime.utcnow()
    if user_id:
        cos.updated_by = user_id
    db.commit()
    db.refresh(cos)
    return cos

def get_document_group_by_id_cos(db: Session, id_cos: str):
    return db.query(models.DocumentGroup).filter(models.DocumentGroup.id_cos == id_cos).first()


def upsert_document(db: Session, id_cos: str, doc_type: str, file_name: str, content: bytes, user_id: int = None, mime_type: str = None):
    query = db.query(models.DocumentForGroup).filter(models.DocumentForGroup.id_cos == id_cos)

    if doc_type == "OTHERS":
        existing = query.filter(
            models.DocumentForGroup.doc_type == "OTHERS",
            models.DocumentForGroup.file_name == file_name
        ).first()
    else:
        existing = query.filter(models.DocumentForGroup.doc_type == doc_type).first()

    if existing:
        existing.file_name = file_name
        existing.file_content = content
        existing.mime_type = mime_type
        existing.uploaded_at = datetime.utcnow()
        if user_id:
            existing.uploaded_by = user_id
        db.commit()
        db.refresh(existing)
        doc = existing
    else:
        doc = models.DocumentForGroup(
            id_cos=id_cos,
            doc_type=doc_type,
            file_name=file_name,
            file_content=content,
            mime_type=mime_type,
            uploaded_at=datetime.utcnow(),
            uploaded_by=user_id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

    # 🔥 update DocumentGroup juga
    cos = db.query(models.DocumentGroup).filter(models.DocumentGroup.id_cos == id_cos).first()
    if cos:
        cos.updated_at = datetime.utcnow()
        if user_id:
            cos.updated_by = user_id
        db.commit()
        db.refresh(cos)

    return doc



def update_document_group_status(db: Session, id_cos: str):
    """
    Update status DocumentGroup:
    - status = 3 kalau semua COS, PFM, MO, WGS sudah ada
    - status = 2 kalau ada tapi belum lengkap
    """
    required_docs = {"COS", "PFM", "MO", "WGS"}  # <--- TAMBAH WGS
    existing_docs = (
        db.query(models.DocumentForGroup.doc_type)
        .filter(models.DocumentForGroup.id_cos == id_cos,
                models.DocumentForGroup.doc_type.in_(required_docs))
        .all()
    )
    existing_doc_types = {d[0] for d in existing_docs}

    cos = db.query(models.DocumentGroup).filter(models.DocumentGroup.id_cos == id_cos).first()
    if cos:
        if required_docs.issubset(existing_doc_types):
            cos.status = 3
        elif existing_doc_types:  
            cos.status = 2
        else:
            cos.status = 1
        cos.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(cos)
        return cos
    return None


def get_eval_circulate_data(db: Session):
    from sqlalchemy.orm import aliased

    created_user = aliased(models.User)   # issuer
    tasked_user = aliased(models.User)    # user yang bertugas

    documents = (
        db.query(
            models.PDFGroupFinal.id_cos.label("id_cos"),        # ambil id_cos asli dari PDFGroupFinal
            models.EvaluationDocumentGroup.id.label("eval_id"), # simpan id evalgroup buat join ke task
            models.EvaluationDocumentGroup.status.label("status"),
            models.EvaluationDocumentGroup.created_time,
            created_user.firstname.label("issuer_name"),
        )
        .join(models.PDFGroupFinal, models.PDFGroupFinal.id == models.EvaluationDocumentGroup.id_pdfFinal)
        .join(created_user, created_user.id == models.EvaluationDocumentGroup.created_by)
        .all()
    )

    result = []
    for doc in documents:
        # Ambil semua task terkait evaluation ini
        tasks = (
            db.query(
                models.EvalTask.task_type,
                tasked_user.firstname.label("tasked_name"),
                models.EvalTask.updated_at,
                models.EvalTask.status
            )
            .join(tasked_user, tasked_user.id == models.EvalTask.tasked_to)
            .filter(models.EvalTask.id_eval == doc.eval_id)
            .all()
        )

        task_map = {t.task_type: t for t in tasks}

        result.append({
            "id_cos": doc.id_cos,  # id_cos asli (string dari DocumentGroup)
            "status": doc.status,
            "created_at": doc.created_time.strftime("%d-%b-%y"),
             "issuer": task_map.get("ISSUED"),
            "checked": task_map.get("CHECK"),
            "approved": task_map.get("APPROVE"),
            "qa_checked": task_map.get("QA_CHECK"),
            "qa_approved": task_map.get("QA_APPROVE"),
        })

    return result



def get_ready_document_groups_for_circulate(db: Session):
    return (
        db.query(models.DocumentGroup)
        .filter(models.DocumentGroup.status == 3)
        .all()
    )


def get_users_by_roles(db: Session, roles: list[int]):
    return (
        db.query(models.User)
        .filter(models.User.role_id.in_(roles))
        .all()
    )

def create_evaluation_with_tasks(db: Session, id_cos: str, issuer_id: int, task_assignments: dict):
    # cari PDFGroupFinal dari id_cos
    pdf_final = db.query(models.PDFGroupFinal).filter_by(id_cos=id_cos).first()
    if not pdf_final:
        return None

    eval_group = models.EvaluationDocumentGroup(
        id_pdfFinal=pdf_final.id,
        status=2,  # default status group = In Progress
        created_time=datetime.utcnow(),
        created_by=issuer_id,
        updated_time=datetime.utcnow(),
        updated_by=issuer_id,
        update_program="Issued complete document"
    )
    db.add(eval_group)
    db.commit()
    db.refresh(eval_group)

    # 🔥 Tambahkan task ISSUED otomatis → status 4 (Done)
    issued_task = models.EvalTask(
        id_eval=eval_group.id,
        task_type="ISSUED",
        tasked_to=issuer_id,   # issuer langsung
        status=5,              # ✅ DONE
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(issued_task)

    # simpan tasks lain dari form
    for task_type, user_id in task_assignments.items():
        if user_id:
            # default status
            default_status = 1  # New
            if task_type == "CHECK":
                default_status = 2  # ✅ Belum di check

            task = models.EvalTask(
                id_eval=eval_group.id,
                task_type=task_type,
                tasked_to=user_id,
                status=default_status,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(task)

    db.commit()
    return eval_group

def get_available_cos_for_evaluation(db: Session):
    EvalGroup = aliased(models.EvaluationDocumentGroup)

    results = (
        db.query(
            models.DocumentGroup.id_cos,
            models.DocumentGroup.status,
            models.User.firstname.label("issuer")
        )
        .join(models.PDFGroupFinal, models.PDFGroupFinal.id_cos == models.DocumentGroup.id_cos)
        .outerjoin(EvalGroup, EvalGroup.id_pdfFinal == models.PDFGroupFinal.id)
        .join(models.User, models.DocumentGroup.created_by == models.User.id, isouter=True)
        .filter(EvalGroup.id.is_(None))  # exclude yang sudah ada evaluation
        .all()
    )

    status_map = {
        1: ("Draft", "gray"),
        2: ("Incomplete", "orange"),
        3: ("Complete - Ready to Approve", "green"),
        4: ("Complete - Waiting to Approval", "blue"),
        5: ("Closed", "red"),
    }

    return [
        {
            "id_cos": r.id_cos,
            "status": r.status,
            "status_text": status_map.get(r.status, ("Unknown", "gray"))[0],
            "status_class": status_map.get(r.status, ("Unknown", "gray"))[1],
            "issuer": r.issuer or "-"
        }
        for r in results
    ]


def get_detail_circulate(db: Session, id_cos: str):
    from sqlalchemy.orm import aliased

    issuer = aliased(models.User)
    tasked_user = aliased(models.User)

    # Ambil evaluation group by cos
    eval_group = (
        db.query(
            models.EvaluationDocumentGroup,
            models.DocumentGroup.id_cos,
            issuer.firstname.label("issuer_name")
        )
        .join(models.PDFGroupFinal, models.PDFGroupFinal.id == models.EvaluationDocumentGroup.id_pdfFinal)
        .join(models.DocumentGroup, models.DocumentGroup.id_cos == models.PDFGroupFinal.id_cos)
        .join(issuer, issuer.id == models.EvaluationDocumentGroup.created_by)
        .filter(models.DocumentGroup.id_cos == id_cos)
        .order_by(models.EvaluationDocumentGroup.created_time.desc())
        .first()
    )

    if not eval_group:
        return None

    # Ambil semua task
    tasks = (
        db.query(
            models.EvalTask.task_type,
            tasked_user.firstname.label("tasked_name"),
            models.EvalTask.status,
            models.EvalTask.updated_at
        )
        .join(tasked_user, tasked_user.id == models.EvalTask.tasked_to)
        .filter(models.EvalTask.id_eval == eval_group.EvaluationDocumentGroup.id)
        .all()
    )

    return {
        "id_cos": eval_group.id_cos,
        "created_time": eval_group.EvaluationDocumentGroup.created_time,
        "issuer": eval_group.issuer_name,
        "status": eval_group.EvaluationDocumentGroup.status,
        "before_state": eval_group.EvaluationDocumentGroup.update_program,
        "tasks": tasks
    }

def is_cos_already_circulated(db: Session, id_cos: str) -> bool:
    """
    True kalau id_cos sudah ada di EvaluationDocumentGroup (via id_pdfFinal).
    """
    exists = (
        db.query(models.EvaluationDocumentGroup.id)
        .join(models.PDFGroupFinal, models.PDFGroupFinal.id == models.EvaluationDocumentGroup.id_pdfFinal)
        .filter(models.PDFGroupFinal.id_cos == id_cos)
        .first()
    )
    return exists is not None

def get_assigned_evaluations(db: Session, user_id: int):
    issuer = aliased(models.User)

    return (
        db.query(
            models.PDFGroupFinal.id_cos.label("id_cos"),
            issuer.firstname.label("issuer_name"),
            models.EvalTask.created_at.label("created_at"),
            models.EvalTask.updated_at.label("updated_at"),
            models.EvalTask.status.label("task_status"),  # status asli task
        )
        .join(models.EvaluationDocumentGroup, models.EvalTask.id_eval == models.EvaluationDocumentGroup.id)
        .join(models.PDFGroupFinal, models.PDFGroupFinal.id == models.EvaluationDocumentGroup.id_pdfFinal)
        .join(issuer, issuer.id == models.EvaluationDocumentGroup.created_by)
        .filter(models.EvalTask.tasked_to == user_id)
        .all()
    )


def get_revisions_by_cos(db: Session, id_cos: str):
    from sqlalchemy.orm import aliased
    give_to_user = aliased(models.User)

    return (
        db.query(
            models.EvalRevision.id,
            models.EvalRevision.description,
            models.EvalRevision.file_name,
            models.EvalRevision.file_content,
            models.EvalRevision.mime_type,
            models.EvalRevision.status,
            models.EvalRevision.created_at,
            give_to_user.firstname.label("give_to_name")  # ambil nama user
        )
        .join(models.EvalTask, models.EvalTask.id == models.EvalRevision.task_id)
        .join(models.EvaluationDocumentGroup, models.EvaluationDocumentGroup.id == models.EvalTask.id_eval)
        .join(models.PDFGroupFinal, models.PDFGroupFinal.id == models.EvaluationDocumentGroup.id_pdfFinal)
        .outerjoin(give_to_user, give_to_user.id == models.EvalRevision.give_to)
        .filter(models.PDFGroupFinal.id_cos == id_cos)
        .order_by(models.EvalRevision.created_at.desc())
        .all()
    )

def create_revision(db: Session, id_cos: str, description: str, file_name: str,
                    file_content: bytes, mime_type: str, created_by: int,
                    ):
    # cari eval group berdasarkan cos
    eval_group = (
        db.query(models.EvaluationDocumentGroup)
        .join(models.PDFGroupFinal, models.PDFGroupFinal.id == models.EvaluationDocumentGroup.id_pdfFinal)
        .filter(models.PDFGroupFinal.id_cos == id_cos)
        .first()
    )
    if not eval_group:
        return None

    # ambil task sesuai user login (checker/approver yang kasih revisi)
    current_task = (
        db.query(models.EvalTask)
        .filter(
            models.EvalTask.id_eval == eval_group.id,
            models.EvalTask.tasked_to == created_by
        )
        .first()
    )
    if not current_task:
        return None

    # 🔥 otomatis tentukan issuer (pembuat circulate)
    issuer_id = eval_group.created_by  

    # buat revision baru → langsung ditugaskan ke issuer
    new_rev = models.EvalRevision(
        task_id=current_task.id,
        description=description,
        file_name=file_name,
        file_content=file_content,
        mime_type=mime_type,
        status=1,  # New
        created_by=created_by,
        created_at=datetime.utcnow(),
        give_to=issuer_id,
    )
    db.add(new_rev)

    # update status EvalGroup
    eval_group.status = 3  # "Need Revision"
    eval_group.update_program = "Checker send revision"
    eval_group.updated_time = datetime.utcnow()
    eval_group.updated_by = created_by

    # update status task checker → Request Revision
    current_task.status = 3
    current_task.updated_at = datetime.utcnow()

    # update status task ISSUED → jadi 2 (In Progress)
    issued_task = (
        db.query(models.EvalTask)
        .filter(
            models.EvalTask.id_eval == eval_group.id,
            models.EvalTask.task_type == "ISSUED"
        )
        .first()
    )
    if issued_task:
        issued_task.status = 4  # Need to Revision
        issued_task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(new_rev)
    return new_rev
