import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from database import Base


class ExerciseType(str, enum.Enum):
    """Mirrors the Flutter ExerciseType enum."""
    pushup = "pushup"
    squat = "squat"
    jumpingJack = "jumpingJack"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    firebase_uid = Column(String(128), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    workouts = relationship("Workout", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    challenge = relationship("Challenge", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, firebase_uid={self.firebase_uid}, email={self.email})>"


class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exercise_type = Column(Enum(ExerciseType), nullable=False)
    reps = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    client_id = Column(String(128), nullable=True)

    # one client_id per user
    __table_args__ = (
        UniqueConstraint("user_id", "client_id", name="uq_user_client_id"),
        Index("ix_workout_user_timestamp", "user_id", "timestamp"),
    )

    # Relationships
    user = relationship("User", back_populates="workouts")

    def __repr__(self):
        return f"<Workout(id={self.id}, type={self.exercise_type}, reps={self.reps})>"


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exercise_type = Column(Enum(ExerciseType), nullable=False)
    target = Column(Integer, nullable=False)
    unit = Column(String(50), nullable=False, default="Reps")

    # One goal per exercise type per user
    __table_args__ = (
        UniqueConstraint("user_id", "exercise_type", name="uq_user_exercise_goal"),
    )

    # Relationships
    user = relationship("User", back_populates="goals")

    def __repr__(self):
        return f"<Goal(id={self.id}, type={self.exercise_type}, target={self.target})>"


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    is_started = Column(Boolean, nullable=False, default=False)
    start_date = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="challenge")

    def __repr__(self):
        return f"<Challenge(id={self.id}, is_started={self.is_started})>"
