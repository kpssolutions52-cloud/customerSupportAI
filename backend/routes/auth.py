"""
Auth routes: signup and login.
POST /auth/signup - Create company + first user
POST /auth/login - Return JWT
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import secrets

from database import get_db
from models import User, Company
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_user_by_id,
    CurrentUser,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# --- Request/Response schemas ---

class SignupRequest(BaseModel):
    """Signup: company name + first user email/password."""
    company_name: str
    email: EmailStr
    password: str


class SignupResponse(BaseModel):
    """Returned after signup: user id, company id, API key, and JWT."""
    user_id: str
    company_id: str
    company_name: str
    api_key: str
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    company_id: str
    company_name: str
    api_key: str


def generate_api_key() -> str:
    """Generate a secure random API key for the company."""
    return f"cs_{secrets.token_urlsafe(32)}"


@router.post("/signup", response_model=SignupResponse)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    """
    Register a new company and first user.
    Returns JWT and company API key for dashboard and API access.
    """
    # Check email not already used
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    # Create company with unique API key
    api_key = generate_api_key()
    company = Company(name=data.company_name.strip(), api_key=api_key)
    db.add(company)
    db.flush()  # get company.id

    # Create user linked to company
    user = User(
        email=data.email,
        password=hash_password(data.password),
        company_id=company.id,
    )
    db.add(user)
    db.flush()

    db.commit()
    db.refresh(company)
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.id})
    return SignupResponse(
        user_id=user.id,
        company_id=company.id,
        company_name=company.name,
        api_key=company.api_key,
        access_token=access_token,
    )


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email and password. Returns JWT and company info including API key.
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    company = user.company
    access_token = create_access_token(data={"sub": user.id})
    return LoginResponse(
        access_token=access_token,
        user_id=user.id,
        company_id=company.id,
        company_name=company.name,
        api_key=company.api_key,
    )


# Optional: get current user info (for dashboard)
class MeResponse(BaseModel):
    user_id: str
    email: str
    company_id: str
    company_name: str
    api_key: str


@router.get("/me", response_model=MeResponse)
def me(user: CurrentUser):
    """Return current user and company info (requires Bearer token)."""
    return MeResponse(
        user_id=user.id,
        email=user.email,
        company_id=user.company_id,
        company_name=user.company.name,
        api_key=user.company.api_key,
    )
