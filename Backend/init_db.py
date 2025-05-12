# init_db.py

from database import Base, engine
from models import ReceiptItem  # Explicit import is cleaner and safer

def init():
    print("🔧 Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialization complete.")

if __name__ == "__main__":
    init()
