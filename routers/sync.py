from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_or_create_user
from models import User, Workout, Goal, Challenge, ExerciseType
from schemas import (
    SyncUpload,
    SyncDownload,
    UserResponse,
    WorkoutResponse,
    GoalResponse,
    ChallengeResponse,
)

router = APIRouter(prefix="/sync", tags=["Sync"])


@router.post("/upload", response_model=dict)
async def sync_upload(
    payload: SyncUpload,
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload the full app state from the mobile device.

    This is the primary endpoint the mobile app calls during "Sync Now".
    """


    # Sync Workouts
    workouts_created = 0
    workouts_skipped = 0

    for w in payload.workouts:
        try:
            exercise_type = ExerciseType(w.exercise_type)
        except ValueError:
            workouts_skipped += 1
            continue

        # Dedup by client_id
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
                workouts_skipped += 1
                continue

        workout = Workout(
            user_id=user.id,
            exercise_type=exercise_type,
            reps=w.reps,
            timestamp=w.timestamp,
            client_id=w.client_id,
        )
        db.add(workout)
        workouts_created += 1

    # Sync Goals
    goals_synced = 0

    for g in payload.goals:
        try:
            exercise_type = ExerciseType(g.exercise_type)
        except ValueError:
            continue

        result = await db.execute(
            select(Goal).where(
                and_(
                    Goal.user_id == user.id,
                    Goal.exercise_type == exercise_type,
                )
            )
        )
        goal = result.scalar_one_or_none()

        if goal:
            goal.target = g.target
            goal.unit = g.unit
        else:
            goal = Goal(
                user_id=user.id,
                exercise_type=exercise_type,
                target=g.target,
                unit=g.unit,
            )
            db.add(goal)
        goals_synced += 1

    # Sync Challenge
    challenge_synced = False

    if payload.challenge is not None:
        result = await db.execute(
            select(Challenge).where(Challenge.user_id == user.id)
        )
        challenge = result.scalar_one_or_none()

        if challenge:
            challenge.is_started = payload.challenge.is_started
            challenge.start_date = payload.challenge.start_date
        else:
            challenge = Challenge(
                user_id=user.id,
                is_started=payload.challenge.is_started,
                start_date=payload.challenge.start_date,
            )
            db.add(challenge)
        challenge_synced = True

    await db.flush()

    return {
        "status": "ok",
        "workouts_created": workouts_created,
        "workouts_skipped": workouts_skipped,
        "goals_synced": goals_synced,
        "challenge_synced": challenge_synced,
    }


@router.get("/download", response_model=SyncDownload)
async def sync_download(
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Download the complete user state for restoring on a fresh install.

    Returns all workouts, goals, and challenge state for the user.
    """
    # Fetch workouts
    result = await db.execute(
        select(Workout)
        .where(Workout.user_id == user.id)
        .order_by(Workout.timestamp.desc())
    )
    workouts = result.scalars().all()

    # Fetch goals
    result = await db.execute(
        select(Goal).where(Goal.user_id == user.id)
    )
    goals = result.scalars().all()

    # Fetch challenge
    result = await db.execute(
        select(Challenge).where(Challenge.user_id == user.id)
    )
    challenge = result.scalar_one_or_none()

    return SyncDownload(
        user=UserResponse(
            id=user.id,
            firebase_uid=user.firebase_uid,
            email=user.email,
            display_name=user.display_name,
            created_at=user.created_at,
            updated_at=user.updated_at,
        ),
        workouts=[
            WorkoutResponse(
                id=w.id,
                exercise_type=w.exercise_type.value,
                reps=w.reps,
                timestamp=w.timestamp,
                client_id=w.client_id,
            )
            for w in workouts
        ],
        goals=[
            GoalResponse(
                id=g.id,
                exercise_type=g.exercise_type.value,
                target=g.target,
                unit=g.unit,
            )
            for g in goals
        ],
        challenge=ChallengeResponse(
            id=challenge.id,
            is_started=challenge.is_started,
            start_date=challenge.start_date,
        ) if challenge else None,
    )
