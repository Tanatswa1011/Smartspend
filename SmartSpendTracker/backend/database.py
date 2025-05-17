import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Supabase PostgreSQL URL
DATABASE_URL = "postgresql://postgres:MySecurePassword1234@db.hhxalltcodwmscigahmx.supabase.co:5432/postgres"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
