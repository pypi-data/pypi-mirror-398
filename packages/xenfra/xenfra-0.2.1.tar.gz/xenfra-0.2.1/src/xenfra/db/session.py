# src/xenfra/db/session.py

from sqlmodel import create_engine, Session, SQLModel
import os

# For now, we will use a simple SQLite database for ease of setup.
# In production, this should be a PostgreSQL database URL from environment variables.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./xenfra.db")

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
