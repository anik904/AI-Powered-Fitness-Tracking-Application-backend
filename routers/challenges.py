from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_or_create_user
from models import User, Challenge
from schemas import ChallengeResponse

router = APIRouter(prefix="/challenges", tags=["Challenges"])


@router.get("/", response_model=ChallengeResponse | None)
async def get_challenge(
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current 30-day challenge state for a user."""
    result = await db.execute(
        select(Challenge).where(Challenge.user_id == user.id)
    )
    challenge = result.scalar_one_or_none()

    if challenge is None:
        return None

    return ChallengeResponse(
        id=challenge.id,
        is_started=challenge.is_started,
        start_date=challenge.start_date,
    )


@router.post("/start", response_model=ChallengeResponse, status_code=201)
async def start_challenge(
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new 30-day challenge.
    If one already exists, it restarts with a new start_date.
    """
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(Challenge).where(Challenge.user_id == user.id)
    )
    challenge = result.scalar_one_or_none()

    if challenge:
        challenge.is_started = True
        challenge.start_date = now
    else:
        challenge = Challenge(
            user_id=user.id,
            is_started=True,
            start_date=now,
        )
        db.add(challenge)

    await db.flush()
    await db.refresh(challenge)

    return ChallengeResponse(
        id=challenge.id,
        is_started=challenge.is_started,
        start_date=challenge.start_date,
    )


@router.post("/reset", status_code=204)
async def reset_challenge(
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Reset the 30-day challenge.
    Sets is_started=False and clears start_date (mirrors resetChallenge in the app).
    """
    result = await db.execute(
        select(Challenge).where(Challenge.user_id == user.id)
    )
    challenge = result.scalar_one_or_none()

    if challenge:
        challenge.is_started = False
        challenge.start_date = None

