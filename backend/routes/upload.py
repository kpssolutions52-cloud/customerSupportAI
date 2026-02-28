"""
Upload route: POST /upload
Upload knowledge base documents for the company (requires JWT).
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from auth import CurrentUser
from database import get_db
from models import Document
from db import add_documents_to_kb

router = APIRouter(tags=["upload"])


@router.post("/upload")
def upload_documents(
    file: UploadFile = File(...),
    user: CurrentUser = ...,
    db: Session = Depends(get_db),
):
    """
    Upload a text file; content is split into chunks and added to the company's
    Chroma knowledge base. Also stored in PostgreSQL (documents table).
    Requires Bearer token (logged-in user).
    """
    company_id = user.company_id
    if not file.filename or not file.filename.lower().endswith((".txt", ".md", ".csv")):
        raise HTTPException(
            status_code=400,
            detail="Upload a .txt, .md, or .csv file",
        )
    content = file.file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text")
    if not text.strip():
        raise HTTPException(status_code=400, detail="File is empty")
    # Store in PostgreSQL
    doc = Document(company_id=company_id, content=text)
    db.add(doc)
    db.commit()
    # Add to Chroma (chunk and embed)
    count = add_documents_to_kb(company_id, [text])
    return {"status": "ok", "chunks_added": count, "document_id": doc.id}


@router.post("/upload/text")
def upload_text(
    body: dict,
    user: CurrentUser = ...,
    db: Session = Depends(get_db),
):
    """
    Add knowledge base content via JSON body: { "text": "..." }.
    Same as file upload but for programmatic use.
    """
    company_id = user.company_id
    text = body.get("text") or body.get("content") or ""
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=400, detail="Provide 'text' or 'content'")
    doc = Document(company_id=company_id, content=text)
    db.add(doc)
    db.commit()
    count = add_documents_to_kb(company_id, [text])
    return {"status": "ok", "chunks_added": count, "document_id": doc.id}
