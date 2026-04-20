from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from shared.database import get_db
from shared.models.document import Document, DocumentType, DocumentStatus
from shared.schemas.api import DocumentResponse, DocumentCreate, DocumentUpdate

router = APIRouter()


@router.get("/", response_model=list[DocumentResponse])
def list_documents(
    project_id: str | None = None,
    doc_type: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Document)
    if project_id:
        query = query.filter(Document.project_id == project_id)
    if doc_type:
        query = query.filter(Document.doc_type == DocumentType(doc_type))
    return query.order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/", response_model=DocumentResponse)
def create_document(data: DocumentCreate, db: Session = Depends(get_db)):
    doc = Document(
        title=data.title,
        content=data.content,
        external_id=data.external_id,
        doc_type=DocumentType(data.doc_type),
        status=DocumentStatus(data.status),
        source_system=data.source_system,
        author=data.author,
        project_id=data.project_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    doc_type: str = Form("other"),
    author: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload a file and create a document record with its content."""
    content_bytes = await file.read()
    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = content_bytes.decode("latin-1")

    doc = Document(
        title=title or file.filename or "Untitled",
        content=content,
        doc_type=DocumentType(doc_type),
        status=DocumentStatus.DRAFT,
        source_system="web_upload",
        author=author,
        project_id=project_id if project_id else None,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: str, data: DocumentUpdate, db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    update_data = data.model_dump(exclude_unset=True)
    if "doc_type" in update_data:
        update_data["doc_type"] = DocumentType(update_data["doc_type"])
    if "status" in update_data:
        update_data["status"] = DocumentStatus(update_data["status"])

    for key, value in update_data.items():
        setattr(doc, key, value)

    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"detail": "Document deleted"}
