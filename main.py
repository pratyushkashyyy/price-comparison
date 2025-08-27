import requests, json
from details_product import get_details_product, clean_unicode_text
from checkforready import ready_check
from time import sleep
from flask import Flask, jsonify, render_template, request
from model import SessionLocal, Product
from datetime import datetime
import pytz
from fetch_shortcode import get_shortcode
app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    """Add CORS headers to allow requests from all hosts"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


def product_details_api(product_url):
        pageId = get_shortcode(product_url)
        print("Page ID: ", pageId)
        try:
            print(f"Checking readiness for product {pageId}")
            percentage = ready_check(pageId)
            if percentage == 'No product detail steps found':
                percentage = 100
            else:
                while percentage < 90:
                    print(f"Waiting for product to load... {percentage}%")
                    percentage = ready_check(pageId)
                    sleep(1)
        except Exception as e:
                return {'error': f'Failed to check readiness attempts: {str(e)}'}
        if pageId:
            product_details = get_details_product(pageId)
            try:
                short_code = pageId
                db = SessionLocal()
                try:
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
                    print(f"New product stored in database: ID={product.id}, Code={short_code}")
                except Exception as e:
                    db.rollback()
                    print(f"❌ Database storage failed: {e}")
                finally:
                    db.close()       
            except Exception as e:
                    print(f"❌ Database operation failed: {e}")
            return product_details

@app.route("/view", methods=["GET"]) 
def view():
    product_url = request.args.get("url")
    if not product_url:
        return jsonify({"error": "Missing required parameter 'url'"}), 400
    return render_template("response.html", url=product_url)

@app.route("/api", methods=["GET"]) 
def api():
    productUrl = request.args.get("url")
    if not productUrl :
        return jsonify({"error": "Missing required parameter 'productUrl'"}), 400
    db = SessionLocal()
    existing_product = db.query(Product).filter(Product.productUrl == productUrl).first()
    if existing_product:
        print("Product already exists in database")
        pageId = (existing_product.shortCode)
        db.close()
        result = get_details_product(pageId)
        if isinstance(result, str):
            try:
                result = clean_unicode_text(json.loads(result))
                print("Result: ", result)
            except json.JSONDecodeError:
                pass
        return jsonify(result), 200
    else:
        result = product_details_api(productUrl)
        if isinstance(result, str):
            try:
                result = clean_unicode_text(json.loads(result))
            except json.JSONDecodeError:
                pass
        return jsonify(result), 200

@app.route("/products", methods=["GET"])
def get_products():
    """Get all products from database"""
    try:
        db = SessionLocal()
        try:
            products = db.query(Product).all()
            product_list = []
            for product in products:
                product_list.append({
                    'id': product.id,
                    'productUrl': product.productUrl,
                    'shortCode': product.shortCode,
                    'timestamp': product.timestamp.isoformat()
                })
            return jsonify({'products': product_list}), 200
        finally:
            db.close()
    except Exception as e:
        return jsonify({'error': f'Failed to fetch products: {str(e)}'}), 500

@app.route("/products/<short_code>", methods=["GET"])
def get_product_by_code(short_code):
    """Get product by short code"""
    try:
        db = SessionLocal()
        try:
            product = db.query(Product).filter(Product.shortCode == short_code).first()
            if product:
                return jsonify({
                    'id': product.id,
                    'productUrl': product.productUrl,
                    'shortCode': product.shortCode,
                    'timestamp': product.timestamp.isoformat()
                }), 200
            else:
                return jsonify({'error': 'Product not found'}), 404
        finally:
            db.close()
    except Exception as e:
        return jsonify({'error': f'Failed to fetch product: {str(e)}'}), 500

@app.route("/<path:url>", methods=["GET"]) 
def root(url):
    if not url:
        return jsonify({"error": "Missing required parameter 'url'"}), 400
    result = product_details_api(url)
    if isinstance(result, str):
        try:
            result = clean_unicode_text(json.loads(result))
        except json.JSONDecodeError:
            pass
    return jsonify(result), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9999, debug=True)
