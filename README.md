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
- **Image Processing**: Pillow, imagehash, OpenCV (for perceptual hashing and ORB feature matching)

### Key Dependencies

**Backend** (`backend/requirements.txt`):
- FastAPI 0.104.1 - Web framework
- SQLAlchemy 2.0.23 - ORM
- Pydantic 2.5.0 - Data validation
- Pillow 10.3.0 - Image processing
- imagehash 4.3.1 - Perceptual hashing
- opencv-python 4.10.0 - ORB feature matching
- boto3 1.40.x - S3-compatible client (Cloudflare R2 image storage)
- openpyxl 3.1.2 - Excel file parsing
- PyPDF2 3.0.1 - PDF file parsing
- psycopg2-binary 2.9.9 - PostgreSQL driver

**Frontend** (`frontend/package.json`):
- React with Vite 7.x
- React Router DOM
- Axios - HTTP client

## Project Structure

```
Inventory_PO_Web_App/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py          # Database configuration
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── main.py              # FastAPI application
│   │   ├── importers.py         # Excel/PDF import logic
│   │   └── image_similarity.py  # Image deduplication (pHash + ORB)
│   │   └── storage.py           # Image storage (local dev or Cloudflare R2)
│   ├── static/images/           # Uploaded product images (local dev)
│   ├── uploads/                 # Temporary import files
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── api.js               # API client
│   │   ├── App.jsx              # Main application with routing
│   │   ├── App.css              # Global styles
│   │   ├── components/
│   │   │   ├── NavBar.jsx       # Navigation bar
│   │   │   └── ProductCard.jsx  # Product card component
│   │   ├── pages/
│   │   │   ├── ProductList.jsx  # Main product listing
│   │   │   ├── ProductDetail.jsx# Product detail/edit page
│   │   │   ├── Cart.jsx         # Shopping cart view
│   │   │   └── Import.jsx       # Excel/PDF/manual import
│   │   └── contexts/
│   │       └── CartContext.jsx  # Cart state management
│   ├── package.json
│   └── vite.config.js
├── sample_data/
│   └── chinatown_invoice_sample.pdf  # Sample PDF for testing
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

#### CORS / Hosting configuration

The API automatically whitelists `http://localhost:3000`, `http://localhost:5173`, and `https://inventory-po-app.vercel.app`. When deploying to Render (or another host), set the following env vars if you need to customize the allowlist:

```
# Replace the entire allowlist (comma separated). Leave empty to keep defaults.
CORS_ALLOW_ORIGINS=https://inventory-po-app.vercel.app,https://your-custom-domain.com

# Append extra origins without losing the defaults.
CORS_EXTRA_ORIGINS=https://staging.your-domain.com

# Keep *.vercel.app previews (and localhost with random ports) allowed via regex.
# Set to false only if you want to block preview deployments entirely.
ENABLE_VERCEL_PREVIEW_CORS=true
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
6. **Image Upload Deduplication**: Product photos are analyzed with perceptual hashes *and* ORB feature matching. Uploads that are ≥95% similar **and** produce at least **225** high-quality ORB matches (roughly 90 % of the overlapping keypoints we see on near-identical catalog shots) reuse the original file so storage stays lean while still linking the new product to the shared photo. When you know an upload is different (e.g., fixing a mismatched catalog photo), both the Product Detail page and the Manual Input form now include an **“Always save this uploaded image”** toggle that bypasses similarity matching for that submission so you are never stuck with a stale image. These thresholds can be tuned via environment variables (see *Image Similarity Settings* below).

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

# Need a different API port? Point the harness at it:
# TEST_API_BASE_URL=http://localhost:8001/api python ../test_core_functionality.py
```

The test harness seeds its own `TEST-*` products and automatically deletes them afterward, keeping your primary inventory data untouched.

This will test:
- Global reset functionality
- Search functionality
- Product detail updates
- Inline order quantity updates
- Validation
- Cart view and synchronization
- PDF invoice import (Chinatown Supermarket format, including duplicate-skipping)

Image similarity regression scenarios now live exclusively in the lightweight CLI inside `backend/tests/image_similarity_cli.py`. Run that helper to evaluate deduplication behavior without exercising the full HTTP harness.

### One-off image similarity checks

Need to verify whether two images will be treated as duplicates without going through the full API flow? Use the standalone CLI harness that ships with the backend:

```bash
cd /path/to/Inventory_PO_Web_App
source backend/venv/bin/activate
python backend/tests/image_similarity_cli.py \
  backend/static/images/test_01_535f18cb.png \
  backend/static/images/800000_23ae6915.png
```

The script prints:

- The pHash similarity score versus `IMAGE_SIMILARITY_THRESHOLD`
- ORB descriptor counts, total “good” matches, and the configured `FEATURE_MATCH_RATIO`/`FEATURE_MIN_MATCHES`
- A final PASS/FAIL verdict that mirrors the backend’s deduplication rules (`image_similarity_threshold` OR `feature_min_matches`).

Paths can be absolute, relative, or `/static/<filename>` (handy if you want to compare against an already-uploaded product image living under `settings.image_dir`). Override any of the thresholds with `--hash-threshold`, `--feature-ratio`, or `--min-feature-matches` flags to experiment without changing `.env`.

## Data Model

### Products Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Auto-increment primary key |
| `product_id` | String | Unique product identifier (indexed) |
| `name` | String | Product name (indexed) |
| `brand` | String | Brand name (indexed, optional) |
| `price` | Numeric(10,2) | Unit price (default: 0) |
| `stock` | Integer | Current stock quantity (default: 0) |
| `order_qty` | Integer | Order quantity (default: 0, indexed) |
| `image_url` | String | Product image URL (optional). Either `/static/...` (local dev) or an absolute URL (e.g. Cloudflare R2 `https://pub-...r2.dev/...`) |
| `image_hash` | String | Perceptual hash for deduplication (optional) |
| `remarks` | Text | Additional notes (optional) |
| `created_at` | Timestamp | Record creation time |
| `updated_at` | Timestamp | Last update time |

**Indexes**: `product_id` (unique), `(brand, name)` for search optimization, `order_qty` for cart queries.

## Development

### Database Migrations

The application uses SQLAlchemy with automatic table creation. For production, consider using Alembic for migrations (already included in requirements.txt).

### Adding New Features

1. Backend: Add new endpoints in `backend/app/main.py`
2. Frontend: Add new pages in `frontend/src/pages/` and update routing in `App.jsx`

## Production Deployment (Beginner-Friendly, Free Tiers)

This app is designed to be deployable with:
- **Frontend**: Vercel (static hosting)
- **Backend**: Render (FastAPI)
- **Database**: Neon (PostgreSQL)
- **Images**: Cloudflare R2 (persistent object storage)

### Current Production Instances

The live environment uses the free-tier providers listed above:

- **Frontend (Vercel)** – `https://inventory-po-app.vercel.app/`
- **Backend (Render)** – `https://inventory-po-app.onrender.com`
- **Database (Neon.tech PostgreSQL)** – provisioned via Neon; the `DATABASE_URL` Render env var references the current instance.
- **Image Storage (Cloudflare R2)** – managed through the Cloudflare dashboard at `https://dash.cloudflare.com/6b02e0f26ce769dd116b1e095c1266f0/r2/default/buckets/inventory-images`

### Production Environment Variables

**Frontend (Vercel)**:
- `VITE_API_URL=https://<your-backend-domain>` (recommended)  
  The frontend will automatically append `/api` if you forget it.
- (Also OK) `VITE_API_URL=https://<your-backend-domain>/api`

**Backend (Render)**:
- `DATABASE_URL=postgresql://...` (Neon connection string)
- `CORS_ALLOW_ORIGINS=https://<your-frontend-domain>` (comma-separated list if needed)
  - If you don't set it, the backend allows `localhost` and `*.vercel.app` by default.
  - Optional advanced: `CORS_ALLOW_ORIGIN_REGEX=...` for a custom regex allowlist.

If using **Cloudflare R2** for images:
- `R2_ENDPOINT_URL=https://<your-account-id>.r2.cloudflarestorage.com`
- `R2_BUCKET_NAME=inventory-images`
- `R2_ACCESS_KEY_ID=...`
- `R2_SECRET_ACCESS_KEY=...`
- `R2_PUBLIC_BASE_URL=https://pub-....r2.dev`

### Image Similarity Settings

Fine-tune deduplication behavior by adding the following to `.env` (defaults in parentheses):

- `IMAGE_SIMILARITY_THRESHOLD` (default **0.95**) – minimum perceptual-hash similarity (1.0 means identical).
- `FEATURE_MATCH_RATIO` (default **0.55**) – Lowe’s ratio threshold when evaluating ORB keypoints (lower = stricter).
- `FEATURE_MIN_MATCHES` (default **225**) – minimum number of “good” ORB matches required before two uploads are treated as the same photo. With ORB extracting 500 descriptors per image, 225 roughly equals a 90 % structural overlap, so distinct packaging artwork will no longer collapse into a single shared image accidentally.

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
- **Pydantic `Extra inputs are not permitted` for `r2_*` env vars**: The settings loader now ignores unknown environment entries, so you can safely add the five `R2_*` values to `.env`. If you still see this error, ensure you're running version `1.2.13` or later (or pull the latest `backend/app/database.py`).

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
