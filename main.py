from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import auth, workouts, goals, challenges, sync


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    await init_db()
    yield


app = FastAPI(
    title="AI Fitness Tracker API",
    description=(
        "Backend API for the AI-Powered Fitness Tracking mobile app. "
        "Provides data sync, workout tracking, goal management, and "
        "30-day challenge state storage."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for mobile app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth.router)
app.include_router(workouts.router)
app.include_router(goals.router)
app.include_router(challenges.router)
app.include_router(sync.router)


@app.get("/", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AI Fitness Tracker API", "version": "1.0.0"}
