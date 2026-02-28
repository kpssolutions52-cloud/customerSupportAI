"""
Multi-tenant middleware platform — database models.

We store ONLY:
- tenants, users, integration configs, knowledge_documents (file_path), chat_logs.
We do NOT store client business data (orders, customers, invoices); that stays in client systems.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


def generate_uuid():
    """Generate UUID for primary keys."""
    return str(uuid4())


class Tenant(Base):
    """
    Tenant (customer of this middleware platform).
    Each tenant has isolated: knowledge base, integrations, chat logs.
    """
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="tenant")
    integrations = relationship("Integration", back_populates="tenant")
    knowledge_documents = relationship("KnowledgeDocument", back_populates="tenant")
    chat_logs = relationship("ChatLog", back_populates="tenant")

    def __repr__(self):
        return f"<Tenant {self.name}>"


class User(Base):
    """User belongs to a tenant. Used for login and dashboard access."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)  # hashed
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")

    def __repr__(self):
        return f"<User {self.email}>"


class Integration(Base):
    """
    Tenant's connection to their client system (CRM, orders API, custom API).
    We store only config (base_url, api_key, auth_type) — NOT client data.
    """
    __tablename__ = "integrations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False)
    type = Column(String(64), nullable=False)  # e.g. "crm", "orders", "custom_api"
    base_url = Column(String(2048), nullable=False)
    api_key = Column(String(512), nullable=True)  # or token; encrypted in production
    auth_type = Column(String(64), nullable=True)  # e.g. "bearer", "api_key", "basic"
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="integrations")

    def __repr__(self):
        return f"<Integration {self.type} {self.base_url}>"


class KnowledgeDocument(Base):
    """
    Metadata for ingested knowledge base documents per tenant.
    Actual content is embedded in Chroma only; we do not store document body here.
    """
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False)
    file_path = Column(String(1024), nullable=False)  # reference only; content in Chroma
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="knowledge_documents")

    def __repr__(self):
        return f"<KnowledgeDocument {self.file_path}>"


class ChatLog(Base):
    """Chat history per tenant (message + AI response). No client business data."""
    __tablename__ = "chat_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="chat_logs")

    def __repr__(self):
        return f"<ChatLog {self.id[:8]}...>"
