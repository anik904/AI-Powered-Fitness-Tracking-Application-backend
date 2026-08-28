from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models import User
from schemas import UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    Register or update a user after Firebase authentication.
    If the firebase_uid already exists, updates email and display_name.
    """
    result = await db.execute(
        select(User).where(User.firebase_uid == payload.firebase_uid)
    )
    user = result.scalar_one_or_none()

    if user:
        # Update existing user
        user.email = payload.email
        user.display_name = payload.display_name
        user.updated_at = datetime.now(timezone.utc)
    else:
        # Create new user
        user = User(
            firebase_uid=payload.firebase_uid,
            email=payload.email,
            display_name=payload.display_name,
        )
        db.add(user)

    await db.flush()
    await db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get the current user's profile by Firebase UID."""
    return user


@router.delete("/delete", status_code=204)
async def delete_user(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete user account and all associated data (workouts, goals, challenge)."""
    await db.delete(user)

