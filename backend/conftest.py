"""
Pytest configuration and fixtures for testing
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from typing import Generator

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.plan import PlanTopic
from app.api.dependencies import get_current_user


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.
    Creates tables, yields session, then drops tables after test.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """Create a test user in the database"""
    user = User(
        clerk_user_id="test_user_123",
        name="Test User",
        current_applying_role="Software Engineer"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def override_get_db(db_session: Session):
    """Override the get_db dependency to use test database"""
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass  # Don't close, let fixture handle it
    
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def override_get_current_user(test_user: User):
    """Override the get_current_user dependency to use test user"""
    def _get_test_user():
        return test_user
    
    app.dependency_overrides[get_current_user] = _get_test_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def enable_stub_llm(monkeypatch):
    """Automatically enable stub LLM for all tests"""
    from app import config
    monkeypatch.setattr(config.settings, "USE_STUB_LLM", True)


@pytest.fixture(scope="function")
def test_client(override_get_db, override_get_current_user, enable_stub_llm) -> TestClient:
    """Create a test client with overridden dependencies"""
    return TestClient(app)
