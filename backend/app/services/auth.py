from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models import LearningPreferences, StudentProfile, User


def register(db: Session, email: str, password: str, display_name: str) -> User:
    email = email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")
    user = User(email=email, password_hash=hash_password(password), display_name=display_name.strip())
    user.profile = StudentProfile()
    user.preferences = LearningPreferences()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    # Same generic error for unknown email and wrong password (no account enumeration).
    if not user or not verify_password(password, user.password_hash) or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email or password is not correct.")
    user.last_login_at = datetime.now(UTC)
    db.commit()
    return user


def issue_token(user: User) -> str:
    return create_access_token(user.id, user.token_version)


def logout(db: Session, user: User) -> None:
    user.token_version += 1  # revokes all outstanding tokens
    db.commit()
