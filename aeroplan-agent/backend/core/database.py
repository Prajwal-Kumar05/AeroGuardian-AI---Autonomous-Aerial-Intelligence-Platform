"""
AeroPlan-Agent :: Database session management (SQLAlchemy + PostgreSQL)
Falls back to SQLite automatically if PostgreSQL is unreachable, so the
project runs out-of-the-box for demos without requiring a DB server.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.core.config import get_settings

settings = get_settings()

try:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    with engine.connect():
        pass
except Exception:
    # Demo-mode fallback: local SQLite file, zero external dependencies
    engine = create_engine("sqlite:///./aeroplan_demo.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend.models import db_models  # noqa: F401  (ensures models are registered)
    Base.metadata.create_all(bind=engine)
