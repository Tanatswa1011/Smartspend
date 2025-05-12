# models.py

from sqlalchemy import Column, Integer, String, Float
from database import Base

class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id = Column(Integer, primary_key=True, index=True)
    item = Column(String, index=True)
    price = Column(Float)

