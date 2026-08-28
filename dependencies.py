from fastapi import Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User


async def get_current_user(
    firebase_uid: str = Query(..., description="Firebase User UID"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Fetch user by Firebase UID, or raise 404 if not found."""
    result = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please register first via /auth/register",
        )
    return user


async def get_or_create_user(
    firebase_uid: str = Query(..., description="Firebase User UID"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Fetch user by Firebase UID, or auto-create if not yet registered."""
    result = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            firebase_uid=firebase_uid,
            email=f"{firebase_uid}@app.user",
            display_name="Fitness User",
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
    return user

