# Inventory PO Web App

A personal web application for managing product inventory and purchase order (PO) quantities.

## Overview

This application streamlines the process of tracking inventory and creating purchase orders. It features a responsive mobile-friendly interface, robust import capabilities for PDF/Excel invoices, and smart image management to reduce storage usage.

### Key Features

*   **Product Management**: View, search, and sort products. Update stock levels and order quantities inline.
    *   **Responsive grid**: On mobile browsers the product list uses a dense, multi-column layout (2 columns on very small phones, 3 columns on most phones) plus a compact card style for easier scanning.
*   **Shopping Cart**: Dedicated view for products with active order quantities (`order_qty > 0`).
*   **Smart Import**: 
    *   Parse Excel and PDF invoices (specifically optimized for Chinatown Supermarket layouts).
    *   Automatic conflict detection (skips existing product IDs).
    *   Position-based data extraction for reliable parsing of various ID formats.
*   **Image Optimization**: 
    *   Automatic deduplication using Perceptual Hashing (pHash) and ORB feature matching.
    *   Reuses existing image files when uploads are ≥95% similar with sufficient feature matches.
*   **Global Reset**: One-click reset of all stock and order quantities for new cycles.

---

## Technology Stack

### Frontend
*   **Framework**: React (Vite 7.x)
*   **Routing**: React Router DOM
*   **HTTP Client**: Axios

### Backend
*   **Framework**: Python FastAPI
*   **ORM**: SQLAlchemy
*   **Database**: PostgreSQL (Production) / SQLite (Local Dev)
*   **Image Processing**: Pillow, ImageHash, OpenCV (ORB)
*   **Storage**: Local Filesystem (Dev) / Cloudflare R2 (Production)
*   **File Parsing**: PyPDF2 (PDF), OpenPyxl (Excel)

---

## Project Structure

```text
Inventory_PO_Web_App/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── importers.py         # Excel/PDF parsing logic
│   │   ├── image_similarity.py  # Deduplication logic (pHash + ORB)
│   │   └── storage.py           # S3/R2 storage handler
│   ├── static/images/           # Local image storage
│   ├── uploads/                 # Temp storage for imports
│   └── run.py                   # Server entry point
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Page views (List, Detail, Cart, Import)
│   │   └── contexts/            # State management
│   └── vite.config.js
├── sample_data/                 # Test invoices/PDFs
└── test_core_functionality.py   # Integration tests
```

---

## Setup & Installation

### Prerequisites
*   **Python**: 3.8+
*   **Node.js**: 20.19+ or 22.12+ (Required by Vite 7)

### 1. Backend Setup

Navigate to the backend directory and set up the Python environment.

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Configuration (.env):**
Copy the example environment file:
```bash
cp .env.example .env
```
*   **Default (Dev)**: Uses SQLite (`inventory_po.db`) and local image storage.
*   **Production**: Set `DATABASE_URL` (PostgreSQL) and `R2_*` variables.

**Run the Server:**
```bash
# Developer Mode (SQLite + Local Images)
python run.py --dev

# Production Mode (PostgreSQL + R2)
python run.py
```
The API will be available at `http://localhost:8000`.

### 2. Frontend Setup

Open a new terminal and navigate to the frontend directory.

```bash
cd frontend
npm install
npm run dev
```
The application will run at `http://localhost:5173`.

---

## Configuration Details

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | DB Connection string | `sqlite:///./inventory_po.db` |
| `IMAGE_DIR` | Local image storage path | `./static/images` |
| `CORS_ALLOW_ORIGINS`| Allowed CORS origins | `http://localhost:3000`, `*.vercel.app` |

### Image Similarity Settings
Tuning these variables in `.env` controls how aggressive the image deduplication is:

*   `IMAGE_SIMILARITY_THRESHOLD` (Default: **0.95**): Minimum pHash similarity.
*   `FEATURE_MATCH_RATIO` (Default: **0.55**): Lowe’s ratio for ORB keypoints (lower is stricter).
*   `FEATURE_MIN_MATCHES` (Default: **225**): Minimum "good" matches required to consider images identical.

---

## Usage Guide

### PDF Import Format
The system is optimized for **Chinatown Supermarket** invoice layouts:
*   **Fields Parsed**: Item Code (`product_id`), Description (`name`), Price Each (`price`).
*   **Logic**:
    *   Uses a **position-based algorithm** to reliably extract IDs relative to the "Amount" column.
    *   Supports various ID formats: 6-digit numeric, alphanumeric (`GT-099`), letter suffixes (`800460S`), etc.
    *   Merges multi-line descriptions automatically.
    *   **Conflict Handling**: Rows with existing Product IDs are skipped (not overwritten) and reported in the UI.

### Image Deduplication
When uploading a product image:
1.  The server calculates a perceptual hash (pHash) and extracts ORB features.
2.  It compares this against all existing images.
3.  If a match is found (≥95% similarity AND ≥225 feature matches), the **existing file path** is reused.
4.  **Override**: You can toggle "Always save this uploaded image" in the UI to bypass this check if necessary.

### Product Detail Editing
- Edit name, brand, price, stock, order quantity, and remarks inline.
- A dedicated **Update Product ID** button unlocks a guarded editor. After you enter a new ID, a confirmation window summarizes the change (showing both the previous and proposed IDs) so you can double-check before the update is saved.

### Inline Stock & Order Editors
- Update values on the product list without losing focus between keystrokes.
- Changes are submitted when you press `Enter` or click away; `Esc` cancels and restores the last saved value.
- Increment/decrement buttons still send immediate updates and keep the inputs synchronized with the backend.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/products` | List products (search/sort/paginate) |
| `GET` | `/api/products/{id}` | Get product details |
| `POST` | `/api/products` | Create product |
| `PUT` | `/api/products/{id}` | Update product |
| `PATCH` | `/api/products/{id}/[stock\|order-qty]` | Quick update stock/order |
| `GET` | `/api/cart` | Get items with `order_qty > 0` |
| `POST` | `/api/import/[excel\|pdf]` | Import data files |
| `POST` | `/api/products/reset` | Reset all stock/orders to 0 |

---

## Testing

The project includes a comprehensive test suite.

**1. Core Functionality Test**
Tests the full flow: API, DB, resets, and PDF import logic.
```bash
# Ensure backend is running, then:
cd backend
python ../test_core_functionality.py
```
This regression harness covers global resets, search, detail edits (including the product ID confirmation flow and repeated rename cases), inline stock/quantity adjustments, cart synchronization, and the Chinatown PDF importer.

**2. PDF Extraction Test**
Verifies the position-based parser against various ID formats.
```bash
cd backend
python tests/test_pdf_product_ids.py
```

**3. Image Similarity CLI**
Test deduplication logic on specific files without running the server.
```bash
python backend/tests/image_similarity_cli.py path/to/image1.png path/to/image2.png
```

### Website Scraper

The repo also contains a standalone scraper (`scraper/`) that mirrors every
product + image from eshouseware.com without touching the main app logic.

```bash
# Activate your preferred venv first
pip install -r scraper/requirements.txt
playwright install  # required once

python -m es_scraper.cli nav --refresh
python -m es_scraper.cli run --mode sitemap --output scraper/data/product_images
```

Images land in `scraper/data/product_images/`, and `scraper/data/catalog.json`
tracks the metadata (product ID, name, source URL, local path) for downstream
consumers. Products that lack a downloadable hero image are skipped so every row
in the manifest corresponds to an on-disk asset.

### Seeding Production from the Scraper Catalog

Once the scraper has populated `scraper/data/catalog.json`, use the helper below
to push batches of products (and their cached hero images) into the production
Render deployment. The script talks to the same FastAPI surface as the UI, so
R2 uploads, deduplication heuristics, and validation rules all stay in effect.

```bash
# From the repo root (activate backend/venv first if you have one)
source backend/venv/bin/activate
python backend/scripts/import_scraped_catalog.py \
  --api-base https://inventory-po-app.onrender.com/api \
  --limit 10
```

Flags:

* `--api-base` – API origin (with or without `/api`). Defaults to `PROD_API_BASE`.
* `--catalog` – Path to the manifest (`scraper/data/catalog.json` by default).
* `--limit` – Number of SKUs to sync per run (defaults to **10** for safe batches).

Behavior:

* New SKUs are created with zero stock/order quantities while preserving the
  scraped name and description (description is saved under `remarks` alongside
  the product URL for traceability).
* If the SKU already exists in PostgreSQL and already has an image, it is
  skipped entirely.
* If the SKU exists but has no `image_url`, the script uploads the cached hero
  image and attaches it via `PUT /api/products/{id}`.

Because every request flows through the public API, successful runs
automatically save binaries to Cloudflare R2 under the production bucket.

---

## Deployment

### Production Stack
*   **Frontend**: Vercel (Static)
*   **Backend**: Render (Web Service)
*   **Database**: Neon (PostgreSQL)
*   **Images**: Cloudflare R2 (Object Storage)

### Deployment Config
*   **Render**: Set `DATABASE_URL` and `CORS_ALLOW_ORIGINS`.
*   **Vercel**: Set `VITE_API_URL` to your Render backend URL.
*   **R2**: Required env vars: `R2_ENDPOINT_URL`, `R2_BUCKET_NAME`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_PUBLIC_BASE_URL`.

---

## Troubleshooting

*   **SQLite Extensions**: If you encounter `Symbol not found: _sqlite3_enable_load_extension` on macOS, ensure you are using the system Python or a Homebrew-installed Python that supports SQLite extensions.
*   **Node Version**: "Vite requires Node.js..." -> Upgrade to Node 20+.
*   **Port In Use**: `[Errno 48] Address already in use` -> Kill the process on port 8000 or use a different port.

## License

This is a personal project for internal use.
