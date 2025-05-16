import os
import re
import io
import logging
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from PIL import Image, ImageEnhance
import pytesseract
from pydantic import BaseModel
import models
from database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title="SmartSpend API", description="Receipt OCR and Expense Tracker API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class ReceiptItemCreate(BaseModel):
    item: str
    price: float

class ReceiptItemResponse(BaseModel):
    id: int
    item: str
    price: float
    created_at: Optional[str] = None

class ReceiptProcessResponse(BaseModel):
    message: str
    items_found: int
    items: List[dict]
    text: str

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"status": "ok", "message": "SmartSpend API is running"}

@app.post("/upload-receipt/", response_model=ReceiptProcessResponse)
async def upload_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a receipt image to extract items and prices using OCR
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read image file
    try:
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
        
        image = Image.open(io.BytesIO(contents))
        
        # Preprocess image for better OCR results
        image = image.convert('L')  # Convert to grayscale
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)  # Increase contrast
        
        # Perform OCR
        raw_text = pytesseract.image_to_string(image, config="--psm 6")
        
        # Extract items and prices using regex
        items = extract_items(raw_text)
        
        if not items:
            return ReceiptProcessResponse(
                message="No items detected in the receipt",
                items_found=0,
                items=[],
                text=raw_text
            )
        
        # Save items to database
        db_items = []
        for item_data in items:
            db_item = models.ReceiptItem(item=item_data["item"], price=item_data["price"])
            db.add(db_item)
            db_items.append(item_data)
        
        db.commit()
        
        return ReceiptProcessResponse(
            message="Receipt processed successfully",
            items_found=len(items),
            items=items,
            text=raw_text
        )
    
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing receipt: {str(e)}")

@app.get("/receipt-items/", response_model=List[dict])
def get_receipt_items(db: Session = Depends(get_db)):
    """
    Get all receipt items from the database
    """
    items = db.query(models.ReceiptItem).all()
    return [item.to_dict() for item in items]

def extract_items(text: str) -> List[dict]:
    """
    Extract items and prices from receipt text using regex
    """
    # Pattern to match item descriptions followed by prices
    # This pattern looks for:
    # - any text (item name)
    # - followed by optional dots or spaces
    # - followed by an optional $ or € symbol
    # - followed by a price (digits with optional decimal point)
    pattern = r"(.+?)\s*\.{0,}\s*[\$€]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))"
    
    matches = re.findall(pattern, text)
    items = []
    
    for match in matches:
        item_name = match[0].strip()
        # Clean up the price: remove commas, ensure period as decimal separator
        price_str = match[1].replace(',', '.').strip()
        
        # Handle cases with multiple decimal points (take the last one as decimal)
        if price_str.count('.') > 1:
            parts = price_str.split('.')
            price_str = ''.join(parts[:-1]) + '.' + parts[-1]
        
        try:
            price = float(price_str)
            items.append({"item": item_name, "price": price})
        except ValueError:
            logger.warning(f"Could not convert price '{price_str}' to float for item '{item_name}'")
    
    return items

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
