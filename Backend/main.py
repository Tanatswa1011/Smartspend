from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import pytesseract
import io
import re

from models import ReceiptItem
from database import SessionLocal

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Max upload size middleware (5MB)
MAX_SIZE_MB = 5

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    content_length = request.headers.get("Content-Length")
    if content_length and int(content_length) > MAX_SIZE_MB * 1024 * 1024:
        return JSONResponse(status_code=413, content={"detail": "File too large"})
    return await call_next(request)

@app.post("/upload-receipt/")
async def upload_receipt(file: UploadFile = File(...)):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Unsupported file type. Upload an image.")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read image.")

    raw_text = pytesseract.image_to_string(image)
    items = extract_items(raw_text)

    # Save items to database
    db = SessionLocal()
    try:
        for item in items:
            db_item = ReceiptItem(item=item["item"], price=item["price"])
            db.add(db_item)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        db.close()

    return {
        "text": raw_text,
        "items": items
    }

def extract_items(text: str):
    """
    Extracts item names and prices using regex from OCR text.
    Looks for lines like: "Milk..........1.99" or "Bread 2.50"
    """
    lines = text.splitlines()
    items = []

    for line in lines:
        match = re.search(r"(.+?)\s*\.{0,}\s*[\$]?(\d{1,3}(?:,\d{3})*(?:\.\d{2}))", line)
        if match:
            item_name = match.group(1).strip()
            price_str = match.group(2).replace(",", "")
            try:
                price = float(price_str)
                items.append({"item": item_name, "price": price})
            except ValueError:
                continue
    return items

# Run with: python main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
