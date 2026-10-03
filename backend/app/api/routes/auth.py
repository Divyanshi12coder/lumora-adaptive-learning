from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Subject, User
from app.schemas import LoginRequest, PreferencesOut, ProfileUpdate, RegisterRequest, TokenResponse, UserOut
from app.services import auth as auth_service

router = APIRouter(tags=["auth & profile"])


def user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id, email=user.email, display_name=user.display_name, role=user.role,
        avatar=user.profile.avatar, grade_band=user.profile.grade_band,
        favorite_subject_id=user.profile.favorite_subject_id, weekly_goal_days=user.profile.weekly_goal_days,
        preferences=PreferencesOut.model_validate(user.preferences),
    )


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    user = auth_service.register(db, body.email, body.password, body.display_name)
    return TokenResponse(access_token=auth_service.issue_token(user), user=user_out(user))


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, body.email, body.password)
    return TokenResponse(access_token=auth_service.issue_token(user), user=user_out(user))


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    auth_service.logout(db, user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user_out(user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Right to erasure: removes the account and all learning data (cascading FKs)."""
    db.delete(user)
    db.commit()


@router.get("/profile", response_model=UserOut)
def get_profile(user: User = Depends(get_current_user)):
    return user_out(user)


@router.put("/profile", response_model=UserOut)
def update_profile(body: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.display_name is not None:
        user.display_name = " ".join(body.display_name.split())
    for field in ("avatar", "grade_band", "weekly_goal_days"):
        value = getattr(body, field)
        if value is not None:
            setattr(user.profile, field, value)
    if "favorite_subject_id" in body.model_fields_set:
        if body.favorite_subject_id is not None and not db.get(Subject, body.favorite_subject_id):
            from fastapi import HTTPException

            raise HTTPException(404, "Subject not found.")
        user.profile.favorite_subject_id = body.favorite_subject_id
    if body.preferences:
        for field, value in body.preferences.model_dump(exclude_none=True).items():
            setattr(user.preferences, field, value)
    db.commit()
    db.refresh(user)
    return user_out(user)
