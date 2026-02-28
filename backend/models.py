"""
SQLAlchemy models for multi-tenant Customer Support AI.
Tables: users, companies, documents, chat_logs.
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


class Company(Base):
    """
    Tenant: each company has its own knowledge base and API key.
    """
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    api_key = Column(String(64), unique=True, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="company")
    documents = relationship("Document", back_populates="company")
    chat_logs = relationship("ChatLog", back_populates="company")

    def __repr__(self):
        return f"<Company {self.name}>"


class User(Base):
    """
    User belongs to a company. Used for login and dashboard access.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)  # hashed
    company_id = Column(UUID(as_uuid=False), ForeignKey("companies.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="users")

    def __repr__(self):
        return f"<User {self.email}>"


class Document(Base):
    """
    Raw document content per company (also stored in Chroma as chunks).
    Keeps a record in PostgreSQL for audit and re-ingestion.
    """
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    company_id = Column(UUID(as_uuid=False), ForeignKey("companies.id"), nullable=False)
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.id[:8]}...>"


class ChatLog(Base):
    """
    Log of chat messages and AI responses per company (for usage and history).
    """
    __tablename__ = "chat_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    company_id = Column(UUID(as_uuid=False), ForeignKey("companies.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="chat_logs")

    def __repr__(self):
        return f"<ChatLog {self.id[:8]}...>"
