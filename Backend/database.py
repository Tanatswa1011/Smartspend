# database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Replace with your actual credentials and RDS endpoint
DATABASE_URL = "postgresql://smartspend:cfvpEp3SwsuzdiJHmV1t@smartspend-db.cn4kw48ww4h5.eu-north-1.rds.amazonaws.com:5432/smartspend"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
