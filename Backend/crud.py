from models import ReceiptItem
from database import SessionLocal

def insert_receipt_items(items):
    db = SessionLocal()
    try:
        for entry in items:
            item = ReceiptItem(item=entry["item"], price=entry["price"])
            db.add(item)
        db.commit()
    finally:
        db.close()
