from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
import pytesseract
import io
import re
import logging

from models import ReceiptItem
from database import SessionLocal, engine, Base
import pytesseract
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"


# ---------------------- Setup ----------------------

# Create all tables
Base.metadata.create_all(bind=engine)

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI()

# CORS setup - adjust this in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
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

# ---------------------- Upload Endpoint ----------------------

@app.post("/upload-receipt/")
async def upload_receipt(file: UploadFile = File(...)):
    logging.info(f"Received file: {file.filename} with content type: {file.content_type}")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload an image.")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert("L")  # Grayscale
        image = image.point(lambda x: 0 if x < 140 else 255, "1")  # Binarize
    except Exception as e:
        logging.error(f"Image read error: {e}")
        raise HTTPException(status_code=400, detail="Could not read uploaded image.")

    try:
        logging.info("Running OCR...")
        raw_text = pytesseract.image_to_string(image, config="--psm 6")
        logging.info(f"OCR result: {raw_text}")
    except Exception as e:
        logging.error(f"OCR error: {e}")
        raise HTTPException(status_code=500, detail="Error during OCR processing.")


    logging.info(f"OCR Extracted Text:\n{raw_text}")

    items = extract_items(raw_text)
    logging.info(f"Parsed Items: {items}")

    db = SessionLocal()
    try:
        for item in items:
            db_item = ReceiptItem(item=item["item"], price=item["price"])
            db.add(db_item)
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save items to database.")
    finally:
        db.close()

    return {
        "message": "Receipt processed successfully.",
        "items_found": len(items),
        "items": items,
        "text": raw_text
    }

# ---------------------- View Items Endpoint ----------------------

@app.get("/receipt-items/")
def read_items():
    db = SessionLocal()
    try:
        items = db.query(ReceiptItem).all()
        return [{"item": i.item, "price": i.price} for i in items]
    finally:
        db.close()

# ---------------------- Helper Function ----------------------

def extract_items(text: str):
    """
    Extracts item names and prices from receipt OCR text.
    Looks for lines like: "Milk..........1.99" or "Bread 2.50"
    """
    lines = text.splitlines()
    items = []

    for line in lines:
        match = re.search(r"(.+?)\s*\.{0,}\s*[\$€]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))", line)
        if match:
            item_name = match.group(1).strip()
            price_str = match.group(2).replace(",", ".").replace(" ", "")
            try:
                price = float(price_str)
                items.append({"item": item_name, "price": price})
            except ValueError:
                continue
    return items

# ---------------------- Run App ----------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
