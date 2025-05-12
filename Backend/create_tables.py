from database import engine, Base
from models import ReceiptItem

Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully.")
