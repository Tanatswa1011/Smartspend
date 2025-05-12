# database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

DATABASE_URL = "postgresql+psycopg2://smartspend:MySecurePass123!@smartspend-db1.cn4kw48ww4h5.eu-north-1.rds.amazonaws.com:5432/postgres"


# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a scoped session
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Base class for ORM models
Base = declarative_base()
