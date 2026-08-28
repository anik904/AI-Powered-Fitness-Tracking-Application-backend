from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


#  Enums
VALID_EXERCISE_TYPES = {"pushup", "squat", "jumpingJack"}



#  User Schemas
class UserRegister(BaseModel):
    """Register or update a user. Sent after Firebase auth on the client."""
    firebase_uid: str = Field(..., min_length=1, description="Firebase User UID")
    email: str = Field(..., min_length=1)
    display_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    firebase_uid: str
    email: str
    display_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


#  Workout Schemas
class WorkoutCreate(BaseModel):
    """Create a single workout record."""
    exercise_type: str = Field(..., description="pushup | squat | jumpingJack")
    reps: int = Field(..., ge=0)
    timestamp: datetime
    client_id: Optional[str] = Field(
        None,
        description="Unique ID from the client for dedup during sync",
    )


class WorkoutResponse(BaseModel):
    id: int
    exercise_type: str
    reps: int
    timestamp: datetime
    client_id: Optional[str] = None

    model_config = {"from_attributes": True}


class WorkoutBulkCreate(BaseModel):
    """Bulk create workouts for sync."""
    workouts: list[WorkoutCreate]


#  Goal Schemas
class GoalCreate(BaseModel):
    """Create or update an exercise goal."""
    exercise_type: str = Field(..., description="pushup | squat | jumpingJack")
    target: int = Field(..., ge=0)
    unit: str = Field("Reps", description="Reps or sec")


class GoalResponse(BaseModel):
    id: int
    exercise_type: str
    target: int
    unit: str

    model_config = {"from_attributes": True}


#  Challenge Schemas
class ChallengeCreate(BaseModel):
    """Start or update a 30-day challenge."""
    is_started: bool = True
    start_date: Optional[datetime] = None


class ChallengeResponse(BaseModel):
    id: int
    is_started: bool
    start_date: Optional[datetime] = None

    model_config = {"from_attributes": True}


#  Sync Schemas
class SyncUpload(BaseModel):
    """
    Full state upload from the mobile app.
    The client sends its entire local state; the server upserts everything.
    """
    workouts: list[WorkoutCreate] = []
    goals: list[GoalCreate] = []
    challenge: Optional[ChallengeCreate] = None


class SyncDownload(BaseModel):
    """Full state download for restoring on a fresh install."""
    user: UserResponse
    workouts: list[WorkoutResponse] = []
    goals: list[GoalResponse] = []
    challenge: Optional[ChallengeResponse] = None
