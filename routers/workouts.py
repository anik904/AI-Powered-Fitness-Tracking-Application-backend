from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_or_create_user
from models import User, Workout, ExerciseType
from schemas import WorkoutCreate, WorkoutResponse, WorkoutBulkCreate

router = APIRouter(prefix="/workouts", tags=["Workouts"])


@router.get("/", response_model=list[WorkoutResponse])
async def list_workouts(
    user: User = Depends(get_or_create_user),
    limit: int = Query(100, ge=1, le=1000),
    since: datetime | None = Query(None, description="Only return workouts after this ISO timestamp"),
    db: AsyncSession = Depends(get_db),
):
    """List user's workouts, ordered by timestamp descending."""


    query = select(Workout).where(Workout.user_id == user.id)
    if since:
        query = query.where(Workout.timestamp >= since)
    query = query.order_by(Workout.timestamp.desc()).limit(limit)

    result = await db.execute(query)
    workouts = result.scalars().all()

    return [
        WorkoutResponse(
            id=w.id,
            exercise_type=w.exercise_type.value,
            reps=w.reps,
            timestamp=w.timestamp,
            client_id=w.client_id,
        )
        for w in workouts
    ]


@router.post("/", response_model=WorkoutResponse, status_code=201)
async def create_workout(
    payload: WorkoutCreate,
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a single workout record."""
    # Validate exercise type
    try:
        exercise_type = ExerciseType(payload.exercise_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid exercise_type. Must be one of: {[e.value for e in ExerciseType]}",
        )

    # Check for duplicate client_id
    if payload.client_id:
        existing = await db.execute(
            select(Workout).where(
                and_(
                    Workout.user_id == user.id,
                    Workout.client_id == payload.client_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Workout with this client_id already exists")

    workout = Workout(
        user_id=user.id,
        exercise_type=exercise_type,
        reps=payload.reps,
        timestamp=payload.timestamp,
        client_id=payload.client_id,
    )
    db.add(workout)
    await db.flush()
    await db.refresh(workout)

    return WorkoutResponse(
        id=workout.id,
        exercise_type=workout.exercise_type.value,
        reps=workout.reps,
        timestamp=workout.timestamp,
        client_id=workout.client_id,
    )


@router.post("/bulk", response_model=dict, status_code=201)
async def bulk_create_workouts(
    payload: WorkoutBulkCreate,
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk create workouts for sync. Skips duplicates based on client_id.
    Returns count of created and skipped workouts.
    """
    created = 0
    skipped = 0

    for w in payload.workouts:
        try:
            exercise_type = ExerciseType(w.exercise_type)
        except ValueError:
            skipped += 1
            continue

        # Skip duplicates by client_id
        if w.client_id:
            existing = await db.execute(
                select(Workout.id).where(
                    and_(
                        Workout.user_id == user.id,
                        Workout.client_id == w.client_id,
                    )
                )
            )
            if existing.scalar_one_or_none() is not None:
                skipped += 1
                continue

        workout = Workout(
            user_id=user.id,
            exercise_type=exercise_type,
            reps=w.reps,
            timestamp=w.timestamp,
            client_id=w.client_id,
        )
        db.add(workout)
        created += 1

    await db.flush()
    return {"created": created, "skipped": skipped}


@router.get("/today", response_model=list[WorkoutResponse])
async def get_today_workouts(
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all workouts for today (UTC)."""
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    result = await db.execute(
        select(Workout)
        .where(
            and_(
                Workout.user_id == user.id,
                Workout.timestamp >= today_start,
            )
        )
        .order_by(Workout.timestamp.desc())
    )
    workouts = result.scalars().all()

    return [
        WorkoutResponse(
            id=w.id,
            exercise_type=w.exercise_type.value,
            reps=w.reps,
            timestamp=w.timestamp,
            client_id=w.client_id,
        )
        for w in workouts
    ]


@router.delete("/clear", status_code=204)
async def clear_workouts(
    user: User = Depends(get_or_create_user),
    since: datetime | None = Query(None, description="Only clear workouts after this ISO timestamp"),
    db: AsyncSession = Depends(get_db),
):
    """Clear workouts for a user. Optionally only clear workouts since a given date."""
    query = select(Workout).where(Workout.user_id == user.id)
    if since:
        query = query.where(Workout.timestamp >= since)

    result = await db.execute(query)
    workouts = result.scalars().all()
    for w in workouts:
        await db.delete(w)

