from model import SessionLocal, Product
from datetime import datetime
import pytz

def add_product(product_url: str, short_code: str):
    """Add a new product to the database"""
    db = SessionLocal()
    try:
        # Create timestamp in Indian timezone
        indian_tz = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(indian_tz)
        
        product = Product(
            productUrl=product_url,
            shortCode=short_code,
            timestamp=timestamp
        )
        
        db.add(product)
        db.commit()
        db.refresh(product)
        print(f"Product added successfully with ID: {product.id}")
        return product
    except Exception as e:
        db.rollback()
        print(f"Error adding product: {e}")
        raise
    finally:
        db.close()

def get_all_products():
    """Get all products from the database"""
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        return products
    finally:
        db.close()

def get_product_by_id(product_id: int):
    """Get a product by its ID"""
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        return product
    finally:
        db.close()

def get_product_by_short_code(short_code: str):
    """Get a product by its short code"""
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.shortCode == short_code).first()
        return product
    finally:
        db.close()

def update_product(product_id: int, product_url: str = None, short_code: str = None):
    """Update a product"""
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            if product_url:
                product.productUrl = product_url
            if short_code:
                product.shortCode = short_code
            product.timestamp = datetime.now(pytz.timezone('Asia/Kolkata'))
            db.commit()
            print(f"Product {product_id} updated successfully")
            return product
        else:
            print(f"Product with ID {product_id} not found")
            return None
    except Exception as e:
        db.rollback()
        print(f"Error updating product: {e}")
        raise
    finally:
        db.close()

def delete_product(product_id: int):
    """Delete a product by ID"""
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            db.delete(product)
            db.commit()
            print(f"Product {product_id} deleted successfully")
            return True
        else:
            print(f"Product with ID {product_id} not found")
            return False
    except Exception as e:
        db.rollback()
        print(f"Error deleting product: {e}")
        raise
    finally:
        db.close()

def print_all_products():
    """Print all products in a formatted way"""
    products = get_all_products()
    if not products:
        print("No products found in the database")
        return
    
    print("\n" + "="*80)
    print(f"{'ID':<5} {'Short Code':<15} {'Timestamp':<25} {'Product URL'}")
    print("="*80)
    
    for product in products:
        timestamp_str = product.timestamp.strftime('%Y-%m-%d %H:%M:%S IST')
        url_preview = product.productUrl[:50] + "..." if len(product.productUrl) > 50 else product.productUrl
        print(f"{product.id:<5} {product.shortCode:<15} {timestamp_str:<25} {url_preview}")
    
    print("="*80)

if __name__ == "__main__":
    # Example usage
    print("Database Operations Example")
    print("-" * 30)
    
    # Add some sample products
    add_product("https://example.com/product1", "PROD001")
    add_product("https://example.com/product2", "PROD002")
    
    # Print all products
    print_all_products()
