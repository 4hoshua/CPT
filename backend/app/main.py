"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from .config import settings
from .database import engine, init_db
from .models import User
from .routers import auth, convert
from .security import hash_password


def seed_initial_admin() -> None:
    """Create the initial admin user from env vars if no users exist yet."""
    with Session(engine) as session:
        has_user = session.exec(select(User)).first()
        if has_user is not None:
            return
        admin = User(
            username=settings.initial_admin_username,
            hashed_password=hash_password(settings.initial_admin_password),
        )
        session.add(admin)
        session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_initial_admin()
    yield


app = FastAPI(title="Packet Tracer Extractor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(convert.router)


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
