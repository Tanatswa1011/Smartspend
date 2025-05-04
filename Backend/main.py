from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import pytesseract
import io
import re

app = FastAPI()

# CORS (Allow frontend to access this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional: Limit max upload size (e.g., 5 MB)
MAX_SIZE_MB = 5

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    content_length = request.headers.get("Content-Length")
    if content_length and int(content_length) > MAX_SIZE_MB * 1024 * 1024:
        return JSONResponse(status_code=413, content={"detail": "File too large"})
    return await call_next(request)

@app.post("/upload-receipt/")
async def upload_receipt(file: UploadFile = File(...)):
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Unsupported file type. Upload an image.")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read image.")

    raw_text = pytesseract.image_to_string(image)
    items = extract_items(raw_text)

    return {
        "text": raw_text,
        "items": items
    }

def extract_items(text: str):
    """
    Extracts item names and prices from text using regex.
    Looks for lines like:
    "Milk..........1.99" or "Bread 2.50"
    """
    lines = text.splitlines()
    items = []

    for line in lines:
        # Match item name and price patterns
        match = re.search(r"(.+?)\s*\.{0,}\s*[\$]?(\d{1,3}(?:,\d{3})*(?:\.\d{2}))", line)
        if match:
            item_name = match.group(1).strip()
            price_str = match.group(2).replace(",", "")  # Remove comma from prices
            try:
                price = float(price_str)
                items.append({"item": item_name, "price": price})
            except ValueError:
                continue  # Skip if conversion fails

    return items

# To run the server directly with `python main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

