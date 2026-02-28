"""
Admin routes: view companies and usage.
GET /admin/companies - List all companies (admin only).
For simplicity we use a fixed admin secret in env (ADMIN_SECRET) or first company as admin.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import Company, User, ChatLog

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")


def require_admin(x_admin_secret: str | None = Header(None)) -> None:
    """Validate admin secret header. Raise if missing or wrong."""
    if not ADMIN_SECRET:
        raise HTTPException(500, detail="Admin not configured (ADMIN_SECRET)")
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(403, detail="Forbidden")


@router.get("/companies")
def list_companies(
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    """
    List all companies with basic info and usage (chat count).
    Send header: X-Admin-Secret: <ADMIN_SECRET>
    """
    # Subquery: chat count per company
    usage = (
        db.query(ChatLog.company_id, func.count(ChatLog.id).label("chat_count"))
        .group_by(ChatLog.company_id)
        .subquery()
    )
    companies = (
        db.query(Company, usage.c.chat_count)
        .outerjoin(usage, Company.id == usage.c.company_id)
        .order_by(Company.name)
        .all()
    )
    return [
        {
            "id": c.id,
            "name": c.name,
            "api_key_prefix": c.api_key[:12] + "..." if len(c.api_key) > 12 else c.api_key,
            "chat_count": (chat_count or 0),
        }
        for c, chat_count in companies
    ]


@router.get("/usage")
def usage_summary(
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Total companies, total users, total chat messages."""
    company_count = db.query(func.count(Company.id)).scalar() or 0
    user_count = db.query(func.count(User.id)).scalar() or 0
    chat_count = db.query(func.count(ChatLog.id)).scalar() or 0
    return {
        "companies": company_count,
        "users": user_count,
        "chat_messages": chat_count,
    }
