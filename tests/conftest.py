"""Pytest configuration and fixtures."""

import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.database import get_db
from app.main import app


@pytest.fixture(scope="session")
def temp_db_file():
    """Create a temporary SQLite database file for testing.
    
    Yields:
        str: Path to temporary database file.
    """
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def test_db(temp_db_file):
    """Create a test database with fresh schema for each test.
    
    Yields:
        Session: SQLAlchemy session connected to test database.
    """
    DATABASE_URL = f"sqlite:///{temp_db_file}"
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    yield db
    db.close()
    
    # Clean up tables
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_client(test_db):
    """Create a test FastAPI client with overridden database dependency.
    
    Yields:
        TestClient: FastAPI test client.
    """
    from fastapi.testclient import TestClient
    
    def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()
