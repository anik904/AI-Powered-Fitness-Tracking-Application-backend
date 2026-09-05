from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_or_create_user
from models import User, Goal, ExerciseType
from schemas import GoalCreate, GoalResponse

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.get("/", response_model=list[GoalResponse])
async def list_goals(
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all exercise goals for a user."""
    result = await db.execute(
        select(Goal).where(Goal.user_id == user.id)
    )
    goals = result.scalars().all()

    return [
        GoalResponse(
            id=g.id,
            exercise_type=g.exercise_type.value,
            target=g.target,
            unit=g.unit,
        )
        for g in goals
    ]


@router.post("/", response_model=GoalResponse, status_code=201)
async def create_or_update_goal(
    payload: GoalCreate,
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create or update a goal for an exercise type.
    If a goal already exists for this exercise type, it gets updated.
    """
    # Validate exercise type
    try:
        exercise_type = ExerciseType(payload.exercise_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid exercise_type. Must be one of: {[e.value for e in ExerciseType]}",
        )

    # Check if goal already exists for this exercise type
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
        # Update existing goal
        goal.target = payload.target
        goal.unit = payload.unit
    else:
        # Create new goal
        goal = Goal(
            user_id=user.id,
            exercise_type=exercise_type,
            target=payload.target,
            unit=payload.unit,
        )
        db.add(goal)

    await db.flush()
    await db.refresh(goal)

    return GoalResponse(
        id=goal.id,
        exercise_type=goal.exercise_type.value,
        target=goal.target,
        unit=goal.unit,
    )


@router.get("/{exercise_type}", response_model=GoalResponse)
async def get_goal(
    exercise_type: str,
    user: User = Depends(get_or_create_user),
    db: AsyncSession = Depends(get_db),
):
    """Get goal for a specific exercise type."""
    try:
        ex_type = ExerciseType(exercise_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid exercise_type. Must be one of: {[e.value for e in ExerciseType]}",
        )

    result = await db.execute(
        select(Goal).where(
            and_(
                Goal.user_id == user.id,
                Goal.exercise_type == ex_type,
            )
        )
    )
    goal = result.scalar_one_or_none()

    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found for this exercise type")

    return GoalResponse(
        id=goal.id,
        exercise_type=goal.exercise_type.value,
        target=goal.target,
        unit=goal.unit,
    )

