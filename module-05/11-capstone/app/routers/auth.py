"""
routers/auth.py

Authentication endpoints:
  POST /auth/register  -- create analyst account, return JWT
  POST /auth/login     -- validate credentials, return JWT
  GET  /users/me       -- return authenticated analyst profile

Rate limited: login 5/min (configured in main.py).
"""
from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import DuplicateException
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, TokenResponse, LoginRequest
from app.utils.auth import (
    hash_password, verify_password, create_access_token, get_current_user,
)
from app.utils.background import log_activity

router = APIRouter(prefix="/auth", tags=["Authentication"])
users_router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new analyst account",
    responses={409: {"description": "Email already registered"}},
)
def register(
    payload: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a new analyst account and return a JWT access token.

    - **name**: Full name of the analyst
    - **email**: Must be unique across the firm
    - **password**: Minimum 8 characters, stored as bcrypt hash
    - **role**: analyst (default), pm, or admin
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise DuplicateException("User", "email", payload.email)

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    background_tasks.add_task(
        log_activity,
        action="REGISTER",
        analyst_id=user.id,
        analyst_email=user.email,
        resource_type="user",
        resource_id=user.id,
    )
    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT token",
    responses={401: {"description": "Invalid credentials"}},
)
def login(
    payload: LoginRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Validate analyst credentials and return a JWT access token.

    - **email**: Registered analyst email
    - **password**: Plain-text password (transmitted over HTTPS only)

    Token expires after 8 hours. Include as `Authorization: Bearer <token>` on protected endpoints.
    """
    from fastapi import HTTPException
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id)})
    background_tasks.add_task(
        log_activity,
        action="LOGIN",
        analyst_id=user.id,
        analyst_email=user.email,
        resource_type="user",
        resource_id=user.id,
    )
    return TokenResponse(access_token=token)


@users_router.get(
    "/me",
    response_model=UserResponse,
    summary="Get authenticated analyst profile",
    responses={401: {"description": "Not authenticated"}},
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Return the authenticated analyst's profile.

    Requires a valid JWT in the Authorization header.
    """
    return current_user
