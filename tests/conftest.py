# [Ngày 2] Pytest fixtures — DB test in-memory SQLite + seed data cho regression Day 1

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.v1.deps import get_db
from app.main import app
from app.models import Base, Project, User, Workspace
from app.models.enums import ProjectStatus, UserRole

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Project IDs dùng trong tests/day01/test_labels.py
SEED_PROJECT_IDS = [10, 20, 30, 40, 50]


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Tạo async engine in-memory và schema cho toàn bộ test session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_seed_reference_data)
    yield engine
    await engine.dispose()


def _seed_reference_data(connection) -> None:
    """Seed user, workspace, projects để FK labels.project_id hợp lệ."""
    from sqlalchemy.orm import Session

    session = Session(bind=connection)
    user = User(
        id=1,
        email="test@taskhub.local",
        full_name="Test User",
        hashed_password="hashed",
        role=UserRole.MEMBER,
        is_active=True,
    )
    workspace = Workspace(id=1, name="Test Workspace", owner_id=1)
    session.add(user)
    session.add(workspace)
    session.flush()

    for project_id in SEED_PROJECT_IDS:
        session.add(
            Project(
                id=project_id,
                workspace_id=1,
                name=f"Project {project_id}",
                description="Seed project for tests",
                status=ProjectStatus.ACTIVE,
            )
        )
    session.commit()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncSession:
    """Cung cấp AsyncSession mới cho mỗi test."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(test_engine):
    """HTTP client với get_db override trỏ tới DB test."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
