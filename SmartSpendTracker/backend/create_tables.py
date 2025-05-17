import sys
import os

# Make sure we can import from the root of the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import Base, engine
from backend.models import ReceiptItem  # ✅ Only import what's defined

# Create the tables
Base.metadata.create_all(bind=engine)

print("✅ Tables created successfully.")

