# Flash.co Product Details Scraper & API

A comprehensive Python web application for extracting product details from Flash.co product pages. The system includes a Flask web API, SQLite database storage, and Playwright-based web scraping with intelligent product readiness detection.

## 🚀 Features

- **🌐 Web Scraping**: Automated product data extraction using Playwright
- **📊 Product Details**: Comprehensive product information including prices, ratings, specifications, and AI insights
- **💾 Database Storage**: SQLite database with product URL tracking and shortcode mapping
- **🔍 Smart Detection**: Intelligent product readiness checking before data extraction
- **🌍 Web API**: RESTful Flask API endpoints for easy integration
- **📱 Web Interface**: HTML templates for viewing product data
- **🔄 Caching**: Database-based caching to avoid re-scraping existing products
- **🛡️ Error Handling**: Robust error handling with fallback methods
- **⏰ Timestamp Tracking**: Indian timezone-based product tracking

## 🏗️ Architecture

```
├── main.py                 # Flask web application & API endpoints
├── fetch_shortcode.py      # Playwright-based URL shortcode extraction
├── details_product.py      # Product details scraping & processing
├── checkforready.py        # Product readiness detection
├── model.py               # SQLAlchemy database models
├── database_ops.py        # Database operations
├── requirements.txt       # Python dependencies
├── products.db           # SQLite database
└── templates/
    └── response.html     # Web interface template
```

## 📋 Prerequisites

- **Python 3.8+**
- **Raspberry Pi 4 (4GB RAM recommended)** or equivalent system
- **DietPi OS** (tested and optimized)
- **Internet connection** for web scraping

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd price
```

2. **Create and activate virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Install Playwright browsers:**
```bash
playwright install chromium
```

5. **Initialize the database:**
```bash
python model.py
```

## 🚀 Usage

### Web API

1. **Start the Flask server:**
```bash
python main.py
```

2. **Access the API at:** `http://localhost:5000`

### API Endpoints

#### Get Product Details
```bash
GET /api?url={product_url}
```

**Example:**
```bash
curl "http://localhost:5000/api?url=https://flash.co/product/example"
```

#### View Product in Browser
```bash
GET /view?url={product_url}
```

**Example:**
```bash
curl "http://localhost:5000/view?url=https://flash.co/product/example"
```

#### Get All Products
```bash
GET /products
```

**Example:**
```bash
curl "http://localhost:5000/products"
```

### Direct Python Usage

```python
from fetch_shortcode import get_shortcode
from details_product import get_details_product
from checkforready import ready_check

# Extract shortcode from URL
shortcode = get_shortcode("https://flash.co/product/example")

# Check if product is ready
readiness = ready_check(shortcode)

# Get product details
product_data = get_details_product(shortcode)
```

## 🔧 Configuration

### Database
- **Type**: SQLite
- **File**: `products.db`
- **Timezone**: Asia/Kolkata (IST)
- **Auto-increment**: Product IDs

### Playwright Settings
- **Browser**: Chromium (headless)
- **User Agents**: Rotating realistic user agents
- **Viewport**: 1920x1080
- **Memory Optimization**: Optimized for Raspberry Pi 4

### System Requirements
- **RAM**: 4GB minimum (optimized for Pi 4)
- **Storage**: 8GB+ available space
- **Network**: Stable internet connection

## 📊 Response Format

### Success Response
```json
{
  "product_id": "ABC123",
  "status": "success",
  "data": {
    "name": "Product Name",
    "price": "₹1,999",
    "stores": [...],
    "specifications": [...],
    "rating": "4.5",
    "reviews_count": "1250",
    "ai_summary": "Product description...",
    "key_strengths": [...],
    "key_limitations": [...],
    "score_breakdown": [...],
    "reviews": [...]
  }
}
```

### Error Response
```json
{
  "error": "Error description",
  "status": "failed"
}
```

## 🗄️ Database Schema

### Products Table
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    productUrl TEXT NOT NULL,
    shortCode VARCHAR(50) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🔍 How It Works

1. **URL Input**: User provides Flash.co product URL
2. **Shortcode Extraction**: Playwright extracts product shortcode from URL
3. **Readiness Check**: System waits for product page to fully load
4. **Data Extraction**: Scrapes comprehensive product information
5. **Database Storage**: Stores URL-shortcode mapping with timestamp
6. **Response**: Returns structured JSON data

## 🚨 Performance Considerations

### Raspberry Pi 4 (4GB RAM)
- **Single Chromium Instance**: ✅ Optimal (100-150MB RAM)
- **Concurrent Instances**: ⚠️ 2-3 max with monitoring
- **Memory Usage**: ~300-450MB total recommended
- **CPU**: ARM Cortex-A72 handles scraping well

### Optimization Tips
- Use single instance processing for stability
- Monitor memory usage with `free -h`
- Implement delays between requests
- Use database caching to avoid re-scraping

## 🧪 Testing

### Run Basic Tests
```bash
python -m pytest
```

### Test Playwright
```bash
python -m pytest --headed
```

### Manual Testing
```bash
python main.py
# Then visit http://localhost:5000/view?url=<test_url>
```

## 📁 Project Structure

```
price/
├── main.py                 # Main Flask application
├── fetch_shortcode.py      # URL shortcode extraction
├── details_product.py      # Product data scraping
├── checkforready.py        # Readiness detection
├── model.py               # Database models
├── database_ops.py        # Database operations
├── requirements.txt       # Dependencies
├── products.db           # SQLite database
├── templates/            # HTML templates
│   └── response.html     # Product view template
├── venv/                 # Virtual environment
└── __pycache__/         # Python cache
```

## 🔒 Security & Ethics

- **Rate Limiting**: Implemented to respect Flash.co servers
- **User Agent Rotation**: Prevents detection
- **Error Handling**: Graceful failure without crashing
- **Terms of Service**: Respect website terms and robots.txt

## 🐛 Troubleshooting

### Common Issues

1. **Playwright Installation**
```bash
playwright install chromium
playwright install-deps
```

2. **Memory Issues on Pi 4**
```bash
# Monitor memory
free -h
# Restart if needed
sudo reboot
```

3. **Database Errors**
```bash
# Reinitialize database
python model.py
```

4. **Network Issues**
```bash
# Check internet connection
ping google.com
# Check DNS
nslookup flash.co
```

## 📈 Monitoring

### System Resources
```bash
# Memory usage
free -h

# Process monitoring
htop

# Disk usage
df -h

# Network connections
netstat -tuln
```

### Application Logs
- Check console output for errors
- Monitor database operations
- Track API request/response times

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on Pi 4
5. Submit a pull request

## 📄 License

This project is for educational and research purposes. Please respect the terms of service of the websites you're scraping.

## 🆘 Support

For issues specific to Raspberry Pi 4 or DietPi:
- Check system resources
- Verify Playwright installation
- Monitor memory usage
- Ensure stable internet connection

---

**Built with ❤️ for Raspberry Pi 4 + DietPi**
