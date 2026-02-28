"""
Knowledge base upload route: POST /upload

Input (multipart/form-data):
- tenant_id (form field)
- file (file field)

Flow:
1. Save file under DATA_DIR/{tenant_id}/documents/
2. Call ingest_document(file_path, tenant_id) to store embeddings in Chroma (tenant_{tenant_id})
3. Record KnowledgeDocument metadata (file_path) — no raw business data in DB
"""

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from auth import TenantFromAuth
from database import get_db
from models import KnowledgeDocument
from knowledge.ingest import ingest_document

router = APIRouter(tags=["upload"])


@router.post("/upload")
async def upload_document(
    tenant_id: str = Form(...),
    file: UploadFile = File(...),
    tenant: TenantFromAuth = Depends(),
    db: Session = Depends(get_db),
):
    """
    Upload a document for a tenant's knowledge base.

    Security:
    - Tenant is resolved from X-API-Key or JWT.
    - tenant_id form field must match authenticated tenant.id.
    """
    if str(tenant.id) != tenant_id:
        raise HTTPException(status_code=403, detail="tenant_id does not match credentials")

    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")

    # Save file under DATA_DIR/{tenant_id}/documents/
    data_root = os.getenv("DATA_DIR", "./data")
    docs_dir = Path(data_root) / tenant_id / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename).name  # avoid directory traversal
    dest_path = docs_dir / safe_name

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    with dest_path.open("wb") as f:
        f.write(content)

    # Ingest into Chroma (per-tenant collection)
    try:
        chunks_added = ingest_document(str(dest_path), tenant_id)
    except ValueError as e:
        # Unsupported file type or loader error
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    # Record metadata only (file_path), not raw content
    doc = KnowledgeDocument(tenant_id=tenant_id, file_path=str(dest_path))
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "status": "ok",
        "tenant_id": tenant_id,
        "file_path": str(dest_path),
        "chunks_added": chunks_added,
        "document_id": doc.id,
    }
