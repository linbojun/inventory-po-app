# Inventory PO Web App

A personal web application for managing product inventory and purchase order (PO) quantities.

## Overview

This application allows you to:
- View and search all products in a scrollable list (mobile + desktop)
- Update stock and order quantities quickly during daily work
- View a "shopping cart" style view showing only products with `order_qty > 0`
- Import product data from Excel / PDF / manual input
- Reset all stock and order quantities with one click to start a new purchasing cycle

## Technology Stack

- **Frontend**: React (Vite) with React Router
- **Backend**: Python FastAPI
- **Database**: PostgreSQL (or SQLite for local development)
- **API**: RESTful JSON API

## Project Structure

```
Inventory_PO_Web_App/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py      # Database configuration
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── main.py           # FastAPI application
│   │   └── importers.py      # Excel/PDF import logic
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── api.js            # API client
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   └── contexts/         # React contexts
│   └── package.json
├── test_core_functionality.py
├── README.md
└── CHANGELOG.md
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 18+ (for frontend)
- PostgreSQL (optional, SQLite can be used for local development)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database URL and other settings
```

For SQLite (default):
```
DATABASE_URL=sqlite:///./inventory_po.db
```

For PostgreSQL:
```
DATABASE_URL=postgresql://user:password@localhost:5432/inventory_po_db
```

Optional (defaults shown):
```
# Images that are >=95% similar will reuse the same file on disk
IMAGE_SIMILARITY_THRESHOLD=0.95
# ORB matcher ratio threshold + minimum good matches for reuse
FEATURE_MATCH_RATIO=0.75
FEATURE_MIN_MATCHES=15
```

5. Run the backend server:
```bash
python run.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

**Prerequisites**: Node.js 20.19+ or 22.12+ is required (Vite 7.x requirement)

1. Ensure you have Node.js 20+ installed:
```bash
node --version  # Should show v20.19+ or v22.12+
```

If you need to install/upgrade Node.js:
```bash
# Install Node.js 20 via Homebrew
brew install node@20

# Add to PATH (add to ~/.zshrc for persistence)
export PATH="/usr/local/opt/brew/opt/node@20/bin:$PATH"
```

2. Navigate to the frontend directory:
```bash
cd frontend
```

3. Install dependencies:
```bash
npm install
```

4. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173` (or another port if 5173 is busy)

## Usage

### Core Features

1. **Product List**: Browse all products with search and sorting capabilities
2. **Product Detail**: View, edit, and delete full product information. Stock, order quantity, and price inputs now ignore mouse-wheel changes to prevent accidental adjustments during scrolling, deletions are gated behind a confirmation prompt, and clearing the Remarks field now truly removes the stored note.
3. **Cart View**: See all products with `order_qty > 0`
4. **Import**: Upload Excel or PDF files to import products. Manual entry validates product IDs up front with live feedback, blocks submission when duplicates are detected, and disables scroll-wheel changes on numeric fields. PDF import now understands the Chinatown Supermarket invoice layout, maps Item Code → Product ID, Description → Name (including case-pack notations), Price Each → Price automatically, and reports any rows that were skipped because those products already exist in the database.
5. **Reset**: Clear all stock and order quantities to start a new cycle
6. **Image Upload Deduplication**: Product photos are analyzed with perceptual hashes *and* ORB feature matching. Uploads that are ≥95% similar or share enough ORB keypoints (even when padding or cropping changes) reuse the original file so storage stays lean while still linking the new product to the shared photo.

### PDF Import Format

- Upload invoices that follow the `Chinatown Supermarket UT inv ####.pdf` layout.
- The importer reads the `Item Code`, `Description`, and `Price Each` columns and stores them as `product_id`, `name`, and `price` respectively (stock/order quantities remain `0`).
- Multi-line descriptions (including bilingual copy and case-pack callouts) are merged automatically and duplicate item codes keep the last occurrence inside the PDF.
- If the PDF references a product ID that already lives in the database, that row is skipped instead of overwriting the existing record and the duplicate list is returned to the UI so users know what stayed untouched.
- The Import page now renders the skipped list with the existing name, incoming name (when different), and the server-supplied reason so you can reconcile conflicts without digging into logs.
- A reference invoice used by the automated tests lives at `sample_data/chinatown_invoice_sample.pdf`; you can reuse it to validate the workflow manually or extend it with your own pricing.
- **Reliability update (2025-12-17):** PDF rows are now parsed even when the `Item Code` column begins at character index `0`, which previously caused every line to be skipped. The core regression suite exercises this exact invoice so future changes can’t silently break the import path again.

### API Endpoints

- `GET /api/products` - List products (with search, sort, pagination)
- `GET /api/products/{id}` - Get product details
- `DELETE /api/products/{id}` - Permanently delete a product (and its image)
- `POST /api/products` - Create new product
- `PUT /api/products/{id}` - Update product
- `PATCH /api/products/{id}/order-qty` - Quick update order quantity
- `GET /api/cart` - Get cart items (products with order_qty > 0)
- `POST /api/products/reset` - Reset all products
- `POST /api/import/excel` - Import from Excel
- `POST /api/import/pdf` - Import from PDF

## Testing

Install the test dependencies and run the core functionality test suite:

```bash
# Install dependencies (pytest and requests are in backend/requirements.txt)
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Make sure backend is running first (in a separate terminal)
python run.py

# Then run the tests (from backend directory)
python ../test_core_functionality.py

# Or using pytest:
pytest ../test_core_functionality.py
```

The test harness seeds its own `TEST-*` products and automatically deletes them afterward, keeping your primary inventory data untouched.

This will test:
- Global reset functionality
- Search functionality
- Product detail updates
- Inline order quantity updates
- Validation
- Cart view and synchronization
- Image similarity deduplication (covers identical uploads, plus padded vs. cropped versions of the same product photo)
  - **Note**: The test requires `backend/static/images/test_01_535f18cb.png` (a cropped version of `800000_23ae6915.png`). If missing, it can be generated:
    ```bash
    cd backend
    source venv/bin/activate
    python3 -c "from PIL import Image; img = Image.open('static/images/800000_23ae6915.png'); w, h = img.size; img.crop((int(w*0.1), int(h*0.1), int(w*0.9), int(h*0.9))).save('static/images/test_01_535f18cb.png')"
    ```
- PDF invoice import (Chinatown Supermarket format, including duplicate-skipping)

## Development

### Running Tests

The project includes a comprehensive test suite in `test_core_functionality.py`. To run the tests:

1. **Ensure the backend server is running** (tests make HTTP requests to the API):
   ```bash
   cd backend
   source venv/bin/activate
   python run.py
   ```

2. **In a separate terminal, run the tests**:
   ```bash
   # From the project root directory
   cd backend
   source venv/bin/activate
   python ../test_core_functionality.py
   ```

   Or if you prefer to use pytest (though the test file is a standalone script):
   ```bash
   cd backend
   source venv/bin/activate
   pytest ../test_core_functionality.py
   ```

The tests cover core functionality including product CRUD operations, search, cart management, image deduplication, and PDF import.

### Database Migrations

The application uses SQLAlchemy with automatic table creation. For production, consider using Alembic for migrations (already included in requirements.txt).

### Adding New Features

1. Backend: Add new endpoints in `backend/app/main.py`
2. Frontend: Add new pages in `frontend/src/pages/` and update routing in `App.jsx`

## Troubleshooting

### Backend Issues

- **SQLite Compatibility Error**: If you see an error like `Symbol not found: _sqlite3_enable_load_extension`, this is a known issue with Python 3.8 from Homebrew on macOS. Solution:
  - Recreate your virtual environment using system Python (which has proper SQLite support):
    ```bash
    cd backend
    rm -rf venv
    /usr/bin/python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
  
- **Port already in use error**: If you see `[Errno 48] Address already in use`, another instance of the server is running. Fix it:
  ```bash
  # Find and kill processes using port 8000
  lsof -ti:8000 | xargs kill -9
  # Or use a different port by modifying backend/run.py
  ```
  
- **Database connection errors**: Check your `DATABASE_URL` in `.env`. SQLite is the default and should work with system Python.
- **Import errors**: Ensure file formats match expected templates
- **CORS errors**: Check CORS settings in `backend/app/main.py`

### Frontend Issues

- **Node.js version errors**: If you see "Vite requires Node.js version 20.19+ or 22.12+", upgrade Node.js:
  ```bash
  brew install node@20
  export PATH="/usr/local/opt/brew/opt/node@20/bin:$PATH"
  # Add the export line to ~/.zshrc to make it permanent
  ```
  
- **API connection errors**: Ensure backend is running on `http://localhost:8000`
- **Build errors**: Try deleting `node_modules` and reinstalling dependencies

## License

This is a personal project for internal use.

# inventory-po-app
