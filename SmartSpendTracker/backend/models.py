from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.database import Base

class ReceiptItem(Base):
    """
    Model representing an item extracted from a receipt
    """
    __tablename__ = "receipt_items"

    id = Column(Integer, primary_key=True, index=True)
    item = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="receipt_items")

    def to_dict(self):
        """Convert model instance to dictionary"""
        created_time = None
        if self.created_at is not None:
            created_time = self.created_at.isoformat()
        
        category_info = None
        if self.category:
            category_info = {
                "id": self.category.id,
                "name": self.category.name,
                "color": self.category.color
            }
            
        return {
            "id": self.id,
            "item": self.item,
            "price": self.price,
            "category": category_info,
            "created_at": created_time
        }
