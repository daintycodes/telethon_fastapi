from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .config import DATABASE_URL

# Only pass `check_same_thread` when using SQLite; PostgreSQL/others don't accept it.
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args) if connect_args else create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency generator for FastAPI to provide DB sessions.
    
    Yields:
        Session: SQLAlchemy session that is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
