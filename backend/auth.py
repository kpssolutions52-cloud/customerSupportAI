"""
JWT authentication and password hashing.
- Hash passwords with passlib (bcrypt).
- Create/verify JWT with python-jose.
- Dependency get_current_user for protected routes.
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
from models import User, Company

# --- Configuration from env ---
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))  # 7 days

# Password hashing (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Auth schemes: Bearer token (JWT) or API key header
bearer_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_password(password: str) -> str:
    """Hash a plain password for storage."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify plain password against hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """Create JWT with subject (e.g. user id) and expiry."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and validate JWT; return payload or None."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


def get_user_by_id(db: Session, user_id: str) -> User | None:
    """Fetch user by primary key."""
    return db.query(User).filter(User.id == user_id).first()


def get_company_by_api_key(db: Session, api_key: str) -> Company | None:
    """Fetch company by API key (for API-key auth)."""
    return db.query(Company).filter(Company.api_key == api_key).first()


def get_current_user_from_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency: require valid JWT and return current User.
    Use on routes that need login (e.g. upload, dashboard).
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user = get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_company_for_request(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    api_key_header: Annotated[str | None, Depends(api_key_scheme)],
    db: Session = Depends(get_db),
) -> Company:
    """
    Dependency: resolve company either from JWT (current user's company) or from X-API-Key.
    Use on /chat so both dashboard users and API clients can chat.
    """
    # 1) Try API key (for server-to-server / API clients)
    if api_key_header:
        company = get_company_by_api_key(db, api_key_header.strip())
        if company:
            return company
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    # 2) Try JWT (dashboard user)
    if credentials:
        payload = decode_token(credentials.credentials)
        if payload and "sub" in payload:
            user = get_user_by_id(db, payload["sub"])
            if user:
                return user.company
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Provide Bearer token or X-API-Key",
        headers={"WWW-Authenticate": "Bearer"},
    )


# Type alias for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user_from_token)]
CompanyFromAuth = Annotated[Company, Depends(get_company_for_request)]
