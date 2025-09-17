from datetime import datetime
import os
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import case
from weasyprint import HTML
from PyPDF2 import PdfMerger
from sqlalchemy.orm import Session
import io
import base64
from . import models
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image
from reportlab.lib.utils import ImageReader
from app import crud
from .models import GroupOperator, PDFGroupFinal, EvaluationDocument, PDFOPT, DocumentForGroup

def image_to_pdf(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # Resize image agar muat di A4
    width, height = A4
    img_w, img_h = image.size
    ratio = min(width / img_w, height / img_h)
    new_w, new_h = img_w * ratio, img_h * ratio

    # ✅ gunakan ImageReader agar BytesIO bisa diterima
    img_reader = ImageReader(io.BytesIO(image_bytes))
    c.drawImage(img_reader, (width - new_w) / 2, (height - new_h) / 2, new_w, new_h)

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.read()


def generate_final_pdf(db: Session, id_cos: str):
    merger = PdfMerger()

    # Definisikan urutan prioritas
    priority_order = case(
        (DocumentForGroup.doc_type == "COS", 1),
        (DocumentForGroup.doc_type == "PFM", 2),
        (DocumentForGroup.doc_type == "WGS", 3),
        (DocumentForGroup.doc_type == "MO", 4),
        (DocumentForGroup.doc_type == "OTHERS", 5),
        else_=99
    )


    # Ambil dokumen sesuai urutan
    docs = (
        db.query(DocumentForGroup)
        .filter(DocumentForGroup.id_cos == id_cos)
        .order_by(priority_order, DocumentForGroup.uploaded_at.asc())
        .all()
    )

    for doc in docs:
        if not doc.file_content:
            continue

        if doc.mime_type and doc.mime_type.startswith("image/"):
            try:
                pdf_bytes = image_to_pdf(doc.file_content)
                merger.append(io.BytesIO(pdf_bytes))
            except Exception as e:
                print(f"[ERROR] Gagal convert image {doc.file_name}: {e}")
        else:
            merger.append(io.BytesIO(doc.file_content))

    # Operator PDF → tambahkan paling akhir
    group_ops = (
        db.query(GroupOperator, PDFOPT)
        .join(PDFOPT, GroupOperator.pdf_operator_id == PDFOPT.id)
        .filter(GroupOperator.id_cos == id_cos)
        .all()
    )

    for group_op, pdfopt in group_ops:
        try:
            pdf_bytes = base64.b64decode(pdfopt.merged_pdf)
            merger.append(io.BytesIO(pdf_bytes))
        except Exception as e:
            print(f"[ERROR] Gagal decode/append operator {pdfopt.nik}: {e}")

    # Simpan hasil merge
    output_stream = io.BytesIO()
    merger.write(output_stream)
    merger.close()
    final_bytes = output_stream.getvalue()

    # Update / Insert ke PDFGroupFinal
    existing = db.query(PDFGroupFinal).filter(PDFGroupFinal.id_cos == id_cos).first()
    if existing:
        existing.final_pdf = final_bytes
        existing.generated_at = datetime.utcnow()
    else:
        db.add(PDFGroupFinal(id_cos=id_cos, final_pdf=final_bytes))

    db.commit()
    return True