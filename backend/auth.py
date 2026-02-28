"""
JWT authentication and password hashing.
Tenant-scoped: resolve tenant by API key or from JWT (user's tenant).
"""

import os
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import User, Tenant

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_tenant_by_api_key(db: Session, api_key: str) -> Tenant | None:
    """Resolve tenant by API key (for chat / webhook)."""
    return db.query(Tenant).filter(Tenant.api_key == api_key).first()


def get_current_user_from_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_tenant_for_request(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    api_key_header: Annotated[str | None, Depends(api_key_scheme)],
    db: Session = Depends(get_db),
) -> Tenant:
    """Resolve tenant from X-API-Key or JWT (user's tenant)."""
    if api_key_header:
        tenant = get_tenant_by_api_key(db, api_key_header.strip())
        if tenant:
            return tenant
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    if credentials:
        payload = decode_token(credentials.credentials)
        if payload and "sub" in payload:
            user = get_user_by_id(db, payload["sub"])
            if user:
                return user.tenant
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Provide Bearer token or X-API-Key", headers={"WWW-Authenticate": "Bearer"})


CurrentUser = Annotated[User, Depends(get_current_user_from_token)]
TenantFromAuth = Annotated[Tenant, Depends(get_tenant_for_request)]
