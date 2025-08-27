# Product Details API

A Python API for extracting product details from Flash.co product pages. The API provides structured JSON responses for product information including prices, ratings, reviews, specifications, and AI-generated insights.

## Features

- 🔍 Extract product details from Flash.co product pages
- 📊 Get comprehensive product information including:
  - Product name and price
  - Store availability and pricing
  - Product specifications
  - User ratings and reviews
  - AI-generated summaries and insights
  - Key strengths and limitations
- 🛡️ Robust error handling with multiple fallback methods
- 🔄 Automatic retry logic for failed requests
- 📱 RESTful API endpoints

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd price
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Direct Function Usage

```python
from details_product import get_product_details_api, get_multiple_products_api

# Get single product details
result = get_product_details_api("SAiYJTHq")
print(json.dumps(result, indent=2))

# Get multiple products
product_codes = ["SAiYJTHq", "9JZQ-ZyV", "XvOk7gGT"]
results = get_multiple_products_api(product_codes)
print(json.dumps(results, indent=2))
```

### Web API Usage

1. Start the API server:
```bash
python api_example.py
```

2. The server will start on `http://localhost:5000`

#### Available Endpoints

**Get Single Product Details**
```bash
GET /api/product/{product_code}
```

Example:
```bash
curl http://localhost:5000/api/product/SAiYJTHq
```

**Get Product Data Only (Clean Response)**
```bash
GET /api/product/{product_code}/data
```

Example:
```bash
curl http://localhost:5000/api/product/SAiYJTHq/data
```

**Get Multiple Products**
```bash
POST /api/products
Content-Type: application/json

{
  "product_codes": ["SAiYJTHq", "9JZQ-ZyV", "XvOk7gGT"]
}
```

Example:
```bash
curl -X POST http://localhost:5000/api/products \
  -H 'Content-Type: application/json' \
  -d '{"product_codes": ["SAiYJTHq", "9JZQ-ZyV"]}'
```

**Health Check**
```bash
GET /api/health
```

Example:
```bash
curl http://localhost:5000/api/health
```

## Response Format

### Single Product Response
```json
{
  "product_id": "SAiYJTHq",
  "status": "success",
  "error": null,
  "data": {
    "name": "Product Name",
    "price": "₹1,999",
    "stores": [
      {
        "name": "Store Name",
        "price": "₹1,999",
        "marketplace": "N/A"
      }
    ],
    "specifications": [
      {
        "label": "Brand",
        "value": "Brand Name"
      }
    ],
    "rating": "4.5",
    "reviews_count": "1250",
    "ai_summary": "This product offers excellent value...",
    "key_strengths": [
      {
        "heading": "Great Performance",
        "content": "Detailed strength description..."
      }
    ],
    "key_limitations": [
      {
        "heading": "Limited Warranty",
        "content": "Detailed limitation description..."
      }
    ],
    "score_breakdown": [
      "Performance: 9.2",
      "Value: 8.5"
    ],
    "reviews": [
      "User review content...",
      "Another review..."
    ]
  }
}
```

### Multiple Products Response
```json
{
  "status": "success",
  "total_products": 3,
  "successful": 2,
  "failed": 1,
  "products": [
    {
      "product_id": "SAiYJTHq",
      "status": "success",
      "data": { ... }
    },
    {
      "product_id": "9JZQ-ZyV",
      "status": "success", 
      "data": { ... }
    },
    {
      "product_id": "XvOk7gGT",
      "status": "failed",
      "error": "No script data found in response"
    }
  ]
}
```

## Error Handling

The API includes comprehensive error handling:

- **Network errors**: Automatic retry with fallback methods
- **JSON parsing errors**: Multiple parsing strategies (standard JSON, JSON5, regex extraction)
- **Missing data**: Graceful degradation with partial data extraction
- **Invalid product codes**: Clear error messages with details

## Testing

Run the test script to see examples:
```bash
python details_product.py
```

This will demonstrate the API functions with sample product codes.

## Dependencies

- `requests`: HTTP requests
- `beautifulsoup4`: HTML parsing
- `json5`: Extended JSON parsing
- `flask`: Web API framework

## License

This project is for educational purposes. Please respect the terms of service of the websites you're scraping.
