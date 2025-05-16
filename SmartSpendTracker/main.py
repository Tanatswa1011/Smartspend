import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import re
import io
from PIL import Image, ImageEnhance
import pytesseract

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Set up database using SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///smartspend.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Import models and set up database
from backend.database import Base, engine, SessionLocal
from backend.models import ReceiptItem
from models.user import User
from models.category import Category

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize database
# We'll use the engine from the backend.database module 
from backend.database import engine
Base.metadata.create_all(bind=engine)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    try:
        return db.query(User).filter(User.id == int(user_id)).first()
    finally:
        db.close()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        db = get_db()
        try:
            user = db.query(User).filter(User.username == username).first()
            
            if user and user.check_password(password):
                login_user(user, remember=remember)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')
        finally:
            db.close()
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if password != password_confirm:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
            
        db = get_db()
        try:
            existing_user = db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                flash('Username or email already exists', 'danger')
                return render_template('register.html')
                
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            
            db.add(new_user)
            db.commit()
            
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.rollback()
            flash(f'Error creating account: {str(e)}', 'danger')
        finally:
            db.close()
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    db = get_db()
    try:
        if request.method == 'POST':
            name = request.form.get('name')
            color = request.form.get('color')
            
            # Check if category already exists
            existing_category = db.query(Category).filter(Category.name == name).first()
            if existing_category:
                flash('A category with this name already exists', 'danger')
                return redirect(url_for('categories'))
                
            new_category = Category(name=name, color=color)
            db.add(new_category)
            db.commit()
            flash('Category added successfully', 'success')
            return redirect(url_for('categories'))
            
        # GET request - show categories
        all_categories = db.query(Category).all()
        return render_template('categories.html', categories=all_categories)
    finally:
        db.close()
        
@app.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    db = get_db()
    try:
        category = db.query(Category).filter(Category.id == id).first()
        if not category:
            flash('Category not found', 'danger')
            return redirect(url_for('categories'))
            
        if request.method == 'POST':
            name = request.form.get('name')
            color = request.form.get('color')
            
            # Check if another category has the same name
            existing_category = db.query(Category).filter(
                Category.name == name, 
                Category.id != id
            ).first()
            
            if existing_category:
                flash('A category with this name already exists', 'danger')
                return render_template('edit_category.html', category=category)
                
            category.name = name
            category.color = color
            db.commit()
            
            flash('Category updated successfully', 'success')
            return redirect(url_for('categories'))
            
        return render_template('edit_category.html', category=category)
    finally:
        db.close()
        
@app.route('/categories/<int:id>/delete')
@login_required
def delete_category(id):
    db = get_db()
    try:
        category = db.query(Category).filter(Category.id == id).first()
        if not category:
            flash('Category not found', 'danger')
            return redirect(url_for('categories'))
            
        db.delete(category)
        db.commit()
        
        flash('Category deleted successfully', 'success')
        return redirect(url_for('categories'))
    finally:
        db.close()
        
@app.route('/categorize/<int:id>', methods=['GET', 'POST'])
@login_required
def categorize_item(id):
    db = get_db()
    try:
        # Get the receipt item
        item = db.query(ReceiptItem).filter(ReceiptItem.id == id).first()
        if not item:
            flash('Receipt item not found', 'danger')
            return redirect(url_for('dashboard'))
        
        # Get all categories
        categories = db.query(Category).all()
        
        if request.method == 'POST':
            category_id = request.form.get('category_id', '')
            
            # Update category
            if category_id:
                category = db.query(Category).filter(Category.id == int(category_id)).first()
                if not category:
                    flash('Selected category not found', 'danger')
                    return render_template('categorize_item.html', item=item, categories=categories)
                    
                item.category_id = category.id
            else:
                item.category_id = None
                
            db.commit()
            flash('Item categorized successfully', 'success')
            return redirect(url_for('dashboard'))
            
        return render_template('categorize_item.html', item=item, categories=categories)
    finally:
        db.close()

# API Endpoints
@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "SmartSpend API is running"})

@app.route('/api/upload-receipt', methods=['POST'])
def upload_receipt():
    """
    Upload and process a receipt image to extract items and prices using OCR
    """
    try:
        # Check if file exists in request
        if 'file' not in request.files:
            return jsonify({"error": "No file found in request"}), 400
            
        file = request.files['file']
        
        # Validate file type
        if file.content_type and not file.content_type.startswith("image/"):
            return jsonify({"error": "File must be an image"}), 400
        
        # Read image file
        contents = file.read()
        if len(contents) > 5 * 1024 * 1024:  # 5MB limit
            return jsonify({"error": "File size exceeds 5MB limit"}), 400
        
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
            return jsonify({
                "message": "No items detected in the receipt",
                "items_found": 0,
                "items": [],
                "text": raw_text
            })
        
        # Save items to database
        db_session = get_db()
        try:
            db_items = []
            for item_data in items:
                db_item = ReceiptItem(item=item_data["item"], price=item_data["price"])
                db_session.add(db_item)
                db_items.append(item_data)
            
            db_session.commit()
            
            return jsonify({
                "message": "Receipt processed successfully",
                "items_found": len(items),
                "items": items,
                "text": raw_text
            })
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()
    
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}")
        return jsonify({"error": f"Error processing receipt: {str(e)}"}), 500

@app.route('/api/receipt-items', methods=['GET'])
def get_receipt_items():
    """
    Get all receipt items from the database
    """
    try:
        db_session = get_db()
        try:
            items = db_session.query(ReceiptItem).all()
            result = [item.to_dict() for item in items]
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error fetching receipt items: {str(e)}")
            return jsonify({"error": f"Error fetching receipt items: {str(e)}"}), 500
        finally:
            db_session.close()
    except Exception as e:
        logger.error(f"Error with database session: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500

def extract_items(text: str):
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
    app.run(host="0.0.0.0", port=5000, debug=True)