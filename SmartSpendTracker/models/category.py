from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from backend.database import Base

class Category(Base):
    """Category model for receipt items"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    color = Column(String(7), nullable=False, default="#6c757d")  # Default gray color
    
    # Relationships
    receipt_items = relationship("ReceiptItem", back_populates="category")
    
    def to_dict(self):
        """Convert category to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color
        }