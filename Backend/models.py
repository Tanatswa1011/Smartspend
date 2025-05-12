from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base

class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id = Column(Integer, primary_key=True, index=True)
    item = Column(String, index=True)
    price = Column(Float)
    quantity = Column(Integer, default=1)
    currency = Column(String, default="$")  # You can update this per locale
    receipt_id = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
