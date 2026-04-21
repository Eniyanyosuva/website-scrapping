import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()


class Base(DeclarativeBase):
    pass


DEFAULT_DB_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/shopping_agent"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# Fallback for environments without psycopg2 installed.
if DATABASE_URL.startswith("postgresql+psycopg2"):
    try:
        import psycopg2  # noqa: F401
    except ModuleNotFoundError:
        DATABASE_URL = "sqlite:///./shopping_agent.db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
