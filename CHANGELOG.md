# Changelog

All notable changes to the Inventory PO Web App project will be documented in this file.

## [1.2.21] - 2025-12-18

### Added - Explicit dev/prod runtime modes

**Why**: Local contributors wanted a one-line command that forces SQLite + filesystem images without juggling environment variables, while production deployments must continue using PostgreSQL and Cloudflare R2. Tying the behavior to a CLI flag avoids accidental production misconfigurations.

**What**:
- Introduced a `--dev` flag on `backend/run.py` that reloads `.env`, sets `DATABASE_URL` to `SQLITE_DATABASE_URL`, and forces local image storage before FastAPI spins up.
- `app/storage.py` now honors the `APP_MODE`/`FORCE_LOCAL_IMAGE_STORAGE` toggle so R2 uploads/downloads are skipped when dev mode is active.
- Documented the new workflow in `README.md`, highlighting the difference between `python run.py --dev` (SQLite/IMAGE_DIR) and `python run.py` (PostgreSQL/R2).

## [1.2.20] - 2025-12-18

### Added - Inline stock editing from the main list

**Why**: Adjusting inventory counts required opening each Product Detail page, while order quantities were already editable inline. Store operators asked to treat stock the same way so recounts and quick corrections can happen directly from the list view.

**What**:
- Added a dedicated `PATCH /api/products/{id}/stock` route plus a `StockUpdate` schema so FastAPI validates non-negative values before persisting.
- Exposed `productAPI.updateStock` on the frontend and enhanced each product card with the same +/- controls used for order quantities, keeping the grid in sync via the existing refresh hook.
- Expanded `test_core_functionality.py` with new stock-focused test cases (inline update + validation) so the regression suite enforces the behavior, and documented the new flow/API surface in `README.md`.

## [1.2.19] - 2025-12-18

### Fixed - Render deployments now whitelist Vercel by default

**Why**: After deploying the backend to Render, the frontend on Vercel hit `Network Error` because the FastAPI CORS middleware only allowed localhost unless `CORS_ALLOW_ORIGINS` was set manually. This also meant preview deployments (`*.vercel.app`) required constant manual updates.

**What**:
- Expanded the backend CORS helpers so localhost and `https://inventory-po-app.vercel.app` are always allowed by default, even when `CORS_ALLOW_ORIGINS` is left unset. Added `CORS_EXTRA_ORIGINS` to append domains without losing the defaults and `ENABLE_VERCEL_PREVIEW_CORS` to keep the regex-based preview allowlist enabled by default.
- Documented the new environment knobs in `README.md` and `backend/.env.example`, making Render/Vercel configuration copy-pasteable for future deployments.

## [1.2.18] - 2025-12-18

### Updated - Core regression suite focuses on API flows

**Why**: The image deduplication checks in `test_core_functionality.py` depended on large binary fixtures and repeated uploads, slowing down the core health check even when teams only needed confirmation that CRUD, cart, and PDF paths still behaved. The dedicated `backend/tests/image_similarity_cli.py` tool now covers those scenarios directly, so duplicating the work inside the HTTP harness was redundant.

**What**:
- Removed the three image deduplication test cases, related fixtures, and `TEST-IMG-*` cleanup helpers from `test_core_functionality.py`.
- Updated the README’s Testing section to note that image dedup validation now lives in the CLI helper rather than the core regression suite.

## [1.2.16] - 2025-12-18

### Added - Standalone Image Similarity CLI

**Why**: QA and support needed a lightweight way to confirm whether two catalog photos would deduplicate before going through the full product upload flow. Without tooling they had to fire the entire API harness or reproduce uploads manually, which is slow and opaque.

**What**:
- Added `backend/tests/image_similarity_cli.py`, a small test harness that accepts two image paths, computes the project’s pHash/ORB metrics, and reports whether the pair clears `IMAGE_SIMILARITY_THRESHOLD` or `FEATURE_MIN_MATCHES`.
- Documented the new script (usage, thresholds, override flags) in `README.md` under Testing so anyone can run quick spot-checks against `/static/...` files or local samples.

## [1.2.17] - 2025-12-18

### Fixed - Vercel ↔ Render production connectivity (CORS + /api base path)

**Why**: After deploying, the Vercel frontend failed with `AxiosError: Network Error` and browser console messages like `blocked by CORS policy` because (1) the backend CORS default only allowed localhost and (2) it’s easy to misconfigure `VITE_API_URL` without the required `/api` path, resulting in `/products` and `/cart` 404s.

**What**:
- Updated the frontend API client so `VITE_API_URL` can be set to either `https://<backend>` or `https://<backend>/api`; the client normalizes to always call `/api/...` routes.
- Updated backend CORS configuration to allow `localhost` and `*.vercel.app` by default when `CORS_ALLOW_ORIGINS` is not explicitly set, while keeping the option to enforce a strict allowlist via `CORS_ALLOW_ORIGINS` (and optional `CORS_ALLOW_ORIGIN_REGEX`).

## [1.2.15] - 2025-12-18

### Tightened - Image Similarity Thresholds

**Why**: When two products share a handful of similar edges, ORB could still register enough “good” matches to reuse the older photo even though the packaging is clearly different. The team asked for a 90 % similarity requirement so only near-identical photos deduplicate automatically.

**What**:
- Raised the default ORB requirements (Lowe ratio **0.55**, minimum matches **225**) so partial look-alikes no longer collapse into the same stored image, while heavily cropped versions of the same product still clear the bar.
- Added environment hooks (`IMAGE_SIMILARITY_THRESHOLD`, `FEATURE_MATCH_RATIO`, `FEATURE_MIN_MATCHES`) so deployments can tune the heuristics without touching the codebase.
- Documented the stricter defaults and configuration knobs in `README.md`, including guidance on when to override them.

## [1.2.14] - 2025-12-18

### Fixed - Force New Image Uploads When Dedup Misfires

**Why**: Operators could not replace an incorrect product photo because the similarity matcher kept reusing an existing `/static/...` image whenever the packaging looked vaguely alike. Even the "Replace Image" flow would loop back to the wrong asset, leaving the catalog stuck.

**What**:
- Added an explicit `force_new_image` flag to the upload pipeline so FastAPI can skip the deduplication query on demand while still recording the new pHash.
- The Product Detail page and the Manual Input form now surface an “Always save this uploaded image” checkbox (enabled by default whenever a file is selected) so users can intentionally bypass dedup when fixing mismatched photos.
- Extended the regression suite with `test_image_deduplication_force_override`, proving that identical uploads normally reuse the same path but honoring the override stores a brand-new file instead.
- Documented the new toggle and test coverage in `README.md`.

## [1.2.13] - 2025-12-18

### Fixed - Settings accept Cloudflare R2 env vars

**Why**: Adding the newly documented `R2_*` variables to `.env` caused FastAPI to crash on startup with Pydantic's `extra_forbidden` validation error because the `Settings` loader only allowed a hard-coded list of fields.

**What**:
- Updated `backend/app/database.py` so the settings model now ignores unknown environment entries, letting deployment-specific keys like `R2_ENDPOINT_URL` coexist with the existing database/upload knobs.
- Documented the fix in `README.md` under Troubleshooting so anyone who sees the legacy error knows to update.

## [1.2.11] - 2025-12-18

### Added - Cloudflare R2 Image Storage (Production)

**Why**: Local disk storage (`backend/static/images/`) does not work reliably on most free hosting platforms (ephemeral filesystems). Using Cloudflare R2 allows persistent image storage with a generous free tier and no egress fees.

**What**:
- Added an R2 (S3-compatible) storage adapter (`backend/app/storage.py`) and new environment variables (`R2_*`) to upload, fetch, and delete images from R2.
- Updated image upload, deduplication (pHash + ORB), and orphan cleanup flows to work with either local `/static/...` images (dev) or R2 public URLs (production).
- Updated the frontend to support absolute `image_url` values (e.g. `https://pub-...r2.dev/...`) and to use an environment-based API URL (`VITE_API_URL`) for production builds.

## [1.2.12] - 2025-12-18

### Fixed - Deployment Env Var Robustness

**Why**: When productionalizing, it’s easy to paste connection strings from command-line examples (e.g. `psql 'postgresql://...'`) or to copy Cloudflare’s bucket-scoped “S3 API” URL. Both formats can break startup if used verbatim.

**What**:
- Normalized `DATABASE_URL` to tolerate common `psql '...url...'` copy/paste mistakes (strips the `psql` prefix and wrapping quotes) so the backend can start reliably.
- Normalized `R2_ENDPOINT_URL` so it accepts either the bare endpoint (`https://<account>.r2.cloudflarestorage.com`) or Cloudflare’s bucket-scoped URL and still configures boto3 correctly.

## [1.2.10] - 2025-12-18

### Improved - README Documentation

**Why**: The README was missing some important information about the project structure, dependencies, and data model, and had duplicate testing sections.

**What**:
- Added `image_similarity.py` to the project structure documentation
- Added complete Key Dependencies section listing all major backend and frontend packages with versions
- Added Data Model section documenting the `products` table schema including the `image_hash` column
- Expanded project structure to show all frontend components, pages, and contexts
- Added `static/images/`, `uploads/`, and `sample_data/` directories to the structure
- Removed duplicate "Development > Running Tests" section (consolidated with existing Testing section)
- Added Image Processing to Technology Stack (Pillow, imagehash, OpenCV)
- Removed duplicate "# inventory-po-app" heading at end of file

## [1.2.9] - 2025-12-18

### Added - ORB-Assisted Image Similarity & Regression

**Why**: pHash-only matching failed whenever two photos contained different padding or crops (e.g., `test_01_535f18cb.png` vs. `800000_23ae6915.png`). That caused duplicate files even though the subject was identical.

**What**:
- Added OpenCV-powered ORB feature extraction that runs alongside pHash (`app/image_similarity.py`). Uploads now reuse existing files when either the perceptual hash meets the similarity threshold or the ORB matcher finds enough good keypoint matches. Cached descriptors are invalidated when files are deleted so repeated comparisons stay fast.
- Introduced tunable `FEATURE_MATCH_RATIO` and `FEATURE_MIN_MATCHES` settings, wired into `process_uploaded_image()` so FastAPI can transparently choose the best metric while keeping the API surface unchanged.
- Extended the regression suite with a new padded-image scenario that uploads the real `backend/static/images/800000_23ae6915.png` and `test_01_535f18cb.png`, asserting the second product now reuses the first image. Documentation highlights the dual-stage matcher and the new environment knobs.

## [1.2.8] - 2025-12-17

### Added - Image Similarity Deduplication & Regression Coverage

**Why**: Uploaded product photos often duplicate existing images. Storing each copy wastes disk space and complicates cleanup when products share visuals. We also lacked automated coverage to ensure future changes keep deduplication working end-to-end.

**What**:
- Introduced perceptual-hash powered similarity detection via a new `image_similarity.py` helper plus a cached `image_hash` column on `products`. The backend now computes hashes for uploads, reuses any image that is ≥95% similar (configurable through `IMAGE_SIMILARITY_THRESHOLD`), and only deletes files when no products reference them.
- Updated `POST /api/products`, `PUT /api/products/{id}`, and `DELETE /api/products/{id}` to route uploads through the similarity check, persist hash metadata, and safeguard shared files. Added a lightweight schema patcher so existing SQLite/Postgres databases gain the new column automatically on startup.
- Documented the new behavior and environment setting in `README.md`, highlighting that image uploads deduplicate by default.
- Extended `test_core_functionality.py` with a red/blue pixel fixture plus a `test_image_deduplication` case that creates three products via real HTTP calls, asserting that identical uploads reuse the same `image_url` while visually distinct images still produce unique files. The test harness also gained an image-aware creation helper and ensures the new `TEST-IMG-*` IDs are cleaned before/after each run.

## [1.2.7] - 2025-12-17

### Added - Pattern-Aware Chinatown PDF Import & Duplicate Messaging

**Why**: The real `Chinatown Supermarket UT inv 36827` PDF uses multi-line bilingual descriptions, embeds the case-pack note inside the price row, and sometimes fuses the Item Code directly to the extended amount (e.g., `64.80800318`). The prior “best effort” parser could not recover these values, so imports either failed or created garbage products. Users also needed clearer messaging when an imported Item Code already exists, otherwise they were unsure whether anything changed.

**What**:
- Copied the exact sample invoice (`backend/uploads/Chinatown Supermarket UT inv 36827.pdf`) into `sample_data/chinatown_invoice_sample.pdf` so automated tests and developers share the same fixture.
- Rebuilt `app.importers.parse_pdf()` with a Chinatown-specific state machine that detects the invoice header, merges description blocks, prettifies case-pack text, parses Item Codes and Price Each values even when the currency fields stick to the amounts, and gracefully reports duplicate rows inside the PDF itself.
- Fixed `PDF_CURRENCY_PATTERN` so currency detection now works on plain decimals (e.g., `16.20`), which the new parser relies on heavily.
- Updated `/api/import/pdf` consumers by enhancing `frontend/src/pages/Import.jsx` to display each skipped duplicate with the stored name, incoming name (when different), and the server-supplied reason so users immediately see why a row was ignored.
- Refreshed `test_core_functionality.py::test_pdf_import` to assert against real Item Codes `800318`, `800572`, `800600`, and `800601`, including their bilingual names and prices, guaranteeing the parser keeps the exact strings emitted by the invoice.
- Documented the duplicate-messaging behavior and sample invoice location in `README.md` under “PDF Import Format”.

## [1.2.6] - 2025-12-17

### Added - Duplicate-Safe Chinatown PDF Import

**Why**: The new `Chinatown Supermarket UT inv 36827` invoices include bilingual descriptions and case-pack notes that must be preserved, and importing them should never overwrite products that already exist in the catalog. Users also asked to see which rows were skipped so they know what remained untouched.

**What**:
- Extended `_parse_line_by_columns()` so the Description slice now captures the neighboring case-pack column, keeping strings such as `4 PCS / CS` inside the product name exactly as printed on the invoice.
- Updated `/api/import/pdf` to skip rows whose `product_id` is already present in the database, returning a new `skipped_existing` payload that surfaces both the stored and incoming names for each duplicate.
- Surfaced the duplicate list on `frontend/src/pages/Import.jsx` so operators immediately see which rows were ignored.
- Expanded `test_core_functionality.py::test_pdf_import` to re-run the import, assert that every product is reported under `skipped_existing`, and confirm that no unwanted creates/updates occur.
- Documented the duplicate-skipping behavior in `README.md` so future contributors understand the mapping rules and UI signal.

## [1.2.5] - 2025-12-17

### Fixed - PDF Import Ignoring Flush-Left Item Codes

**Why**: The Chinatown invoice layout places the `Item Code` column at character index `0`. The PDF parser treated a column offset of `0` as “missing,” so every product row was discarded and imports failed entirely.

**What**:
- Updated `_parse_line_by_columns()` so column positions equal to `0` are accepted, ensuring we always read the Item Code, Description, and Price Each values from Chinatown invoices.
- Added a regression test (`test_pdf_import`) to `test_core_functionality.py` that uploads `sample_data/chinatown_invoice_sample.pdf` and asserts each row lands in the database with the correct ID, name, and price.
- Noted the reliability fix in `README.md` under “PDF Import Format” so developers know the importer now handles flush-left item codes and that the behavior is covered by automated tests.

## [1.2.4] - 2025-12-17

### Added - Structured PDF Import for Chinatown Invoices

**Why**: Product data is frequently delivered as `Chinatown Supermarket UT` invoices where the Item Code, Description, and Price Each columns must be ingested directly. The previous PDF importer only grabbed the first word or two from each line, producing unusable product IDs and zero-priced rows, and there was no automated regression coverage for the PDF path.

**What**:
- Rebuilt `parse_pdf()` to detect the Item Code / Description / Price Each columns, merge multi-line descriptions, skip footer totals, and convert the Price Each column into a Decimal-backed product price. Duplicate item codes now emit warnings and keep the last occurrence.
- Added a canonical sample invoice at `sample_data/chinatown_invoice_sample.pdf` so both developers and automated tests can reproduce the parser behavior without relying on external files.
- Extended `test_core_functionality.py` with a `test_pdf_import` case that uploads the sample invoice, verifies every product landed with the correct ID, name, and price, and keeps the database clean afterward.
- Documented the supported PDF layout and sample data location in `README.md`, and noted the new regression coverage in the Testing section.

## [1.2.3] - 2025-12-17

### Added - Safer Product Removal and Manual Entry Validation

**Why**: Users needed a reliable way to delete products directly from the Product Detail page, and manual product creation was prone to accidental duplicate IDs that caused backend errors. The manual form’s cancel action also needed clearer styling.

**What**:
- Added a DELETE `/api/products/{id}` endpoint that also removes orphaned image files.
- Extended the Product Detail page with a confirmation-gated “Delete Product” action and wired it to the new API.
- Manual Input form now checks product ID uniqueness before submission, surfaces inline errors, and keeps users on the form until issues are resolved.
- Added real-time product ID validation feedback that disables the submission button until the entered ID is confirmed unique.
- Styled the manual form’s Cancel button with a dark grey treatment to visually offset it from primary actions.
- Updated README.md to document the new delete capability, uniqueness safeguard, and API surface.
- Hardened `test_core_functionality.py` to align duplicate fixtures, wipe any lingering `TEST-*` products before and after each run, and keep the database clean once the suite finishes.
- Normalized backend remark handling so blank submissions persist as `null`, updated the Product Detail API client accordingly, and extended the regression suite to ensure clearing remarks works end-to-end.
- Price input on the Product Detail page now also ignores scroll-wheel adjustments to avoid unintended edits, with documentation updated to match.
- Manual Input form price/stock/order fields ignore scroll-wheel adjustments to keep numeric values stable during form navigation.

## [1.2.2] - 2025-12-17

### Fixed - Prevent Accidental Scroll Edits on Product Detail

**Why**: Users reported that scrolling while focused on the Stock or Order Quantity inputs unintentionally incremented or decremented the values, causing incorrect inventory adjustments.

**What**:
- Updated `frontend/src/pages/ProductDetail.jsx` to cancel the scroll-wheel event before it mutates numeric values and immediately blur the input so page scrolling can resume normally.
- Documented the safer numeric input behavior in `README.md` under the Product Detail feature description and clarified the `requests` dependency needed to run the regression tests.
- Updated `test_core_functionality.py` to accept an optional `brand` argument and submit data using form-encoded payloads so the regression suite stays compatible with the multipart-capable FastAPI endpoints.

## [1.2.1] - 2025-01-XX

### Added - Drag and Drop Image Upload

**Why**: Users requested the ability to drag and drop image files directly onto the image upload area in addition to using the file input button, providing a more intuitive and faster way to upload product images.

**What**:
- **Import Page (Manual Input)**:
  - Added drag-and-drop zone for image uploads
  - Users can now drag image files directly onto the drop zone area
  - Visual feedback when dragging over the drop zone (highlighted border and background)
  - Drop zone is also clickable to trigger file browser
  - Shows preview of selected/dropped image
  - "Remove Image" button to clear selected image before submission

- **Product Detail Page**:
  - Added drag-and-drop functionality to the product image section
  - Users can drag new images directly onto the existing product image to replace it
  - Visual overlay appears when dragging over the image area
  - Maintains existing "Replace Image" button functionality
  - Shows preview of new image before saving
  - "Cancel Replacement" button to revert to original image

**Technical Details**:
- Implemented drag event handlers: `onDragOver`, `onDragLeave`, `onDrop`
- Added visual state management for drag feedback (`isDragging`)
- Reused existing image validation logic for both file input and drag-drop
- Drop zones are clickable to maintain accessibility
- Prevents default browser drag behavior to avoid navigation issues

## [1.2.0] - 2025-01-XX

### Added - Image File Upload Support

**Why**: Users requested the ability to upload local image files for products instead of only providing image URLs. This makes it easier to add product images without needing to host them externally first.

**What**:

#### Backend Changes:
- Updated `POST /api/products` endpoint to accept multipart/form-data with optional image file upload
- Updated `PUT /api/products/{id}` endpoint to accept image file uploads for replacing existing product images
- Added `save_uploaded_image()` helper function that:
  - Validates image file types (JPEG, PNG, GIF, WebP)
  - Generates unique filenames using product_id and UUID
  - Saves images to the configured image directory (`IMAGE_DIR`)
  - Returns relative path stored in database (e.g., `/static/product_id_uuid.jpg`)
- Added `delete_image_file()` helper function to clean up old images when replaced
- Images are stored on the filesystem and served via the existing `/static` endpoint
- Old images are automatically deleted when a product image is replaced

#### Frontend Changes:
- **Import Page (Manual Input)**:
  - Replaced image URL input field with file upload input
  - Added image preview functionality showing selected image before upload
  - Added file validation (type and size checks, max 5MB)
  - Updated form submission to send image file via FormData
  
- **Product Detail Page**:
  - Added "Replace Image" button and file input for uploading new product images
  - Shows preview of newly selected image before saving
  - Displays current product image with proper backend URL prefix
  - Updated save functionality to include image file in update request
  
- **Product Card Component**:
  - Updated to display images using full backend URL (`http://localhost:8000/static/...`)
  - Maintains fallback to placeholder image if no image is set

- **API Client**:
  - Updated `createProduct()` to accept optional image file parameter
  - Updated `updateProduct()` to accept optional image file parameter
  - Both methods now use FormData for multipart/form-data requests

### Technical Details:

**Image Storage**:
- Images are stored in the directory specified by `IMAGE_DIR` environment variable (default: `./static/images`)
- Filename format: `{product_id}_{uuid8}.{ext}` (e.g., `800001_a1b2c3d4.jpg`)
- Database stores relative path: `/static/{filename}` for serving via FastAPI static files

**Image Validation**:
- Allowed formats: JPEG, JPG, PNG, GIF, WebP
- Maximum file size: 5MB
- Frontend validates before upload, backend validates on receipt

**Image Replacement**:
- When updating a product with a new image, the old image file is automatically deleted
- Prevents accumulation of unused image files on the filesystem

## [1.1.1] - 2025-01-XX

### Fixed - Regex Pattern Error in importers.py

**Why**: The `PDF_CURRENCY_PATTERN` regex in `importers.py` had incorrect escaping, causing `re.error: nothing to repeat at position 6` when the module was imported, preventing the backend server from starting.

**What**:
- Fixed the regex pattern from `r"(-?\\$?\\s*\\(?\\d[\\d,]*\\.\\d{2}\\)?)"` to `r"(-?\\\$?\s*\(?\d[\d,]*\.\d{2}\)?)"`
- The issue was with incorrect backslash escaping in the raw string
- Pattern now correctly matches currency values like `$12.34` or `123.45`
- Backend server can now start successfully

### Fixed - Node.js Version Compatibility Issue

**Why**: The frontend uses Vite 7.x which requires Node.js 20.19+ or 22.12+, but the system had Node.js 16.13.1 installed, causing the frontend dev server to fail with version errors.

**What**:
- Installed Node.js 20.19.6 via Homebrew (`brew install node@20`)
- Added Node.js 20 to PATH in `~/.zshrc` to make it the default Node.js version
- Updated README.md with Node.js version requirements and installation instructions
- Frontend can now run successfully with the correct Node.js version

### Fixed - SQLite Compatibility Issue

**Why**: Python 3.8 from Homebrew on macOS has a known SQLite library compatibility issue that causes `ImportError: Symbol not found: _sqlite3_enable_load_extension` when trying to use SQLite. This prevented the server from starting.

**What**:
- Recreated virtual environment using system Python 3.9.6 (which has proper SQLite support) instead of Homebrew Python 3.8
- System Python 3.9.6 includes SQLite 3.43.2 which works correctly
- Updated `.env` file to use SQLite by default (`sqlite:///./inventory_po.db`)
- Added error handling in `database.py` to catch SQLite compatibility errors gracefully with helpful error messages
- Updated README.md with troubleshooting section for this issue
- SQLite is now working correctly and the server can start successfully

### Fixed - Missing .env.example File

**Why**: The README.md instructions referenced copying `.env.example` to `.env`, but the `.env.example` file was missing, causing setup failures for new users.

**What**:
- Created `backend/.env.example` file with all required environment variables:
  - `DATABASE_URL` (with examples for SQLite and PostgreSQL)
  - `UPLOAD_DIR` (directory for uploaded files)
  - `IMAGE_DIR` (directory for product images)
- Added helpful comments explaining each variable
- File includes default values matching the application defaults

### Fixed - Missing database.py and importers.py Files

**Why**: The backend server failed to start with `ModuleNotFoundError: No module named 'app.database'` because the `database.py` and `importers.py` files were missing from the `app/` directory, even though they were referenced in `main.py`.

**What**:
- Recreated `backend/app/database.py` with:
  - Settings class using pydantic-settings for environment variable management
  - Database engine configuration supporting both SQLite and PostgreSQL
  - SessionLocal and get_db function for database session management
  - Automatic directory creation for uploads and images
- Recreated `backend/app/importers.py` with:
  - `parse_excel()` function that parses Excel files with flexible column mapping
  - `parse_pdf()` function for basic PDF text extraction (best-effort parsing)
  - Both functions return tuples of (products, errors) as expected by the API endpoints
  - Error handling and validation for imported data

## [1.1.0] - 2025-01-XX

### Added - Manual Product Creation Form

**Why**: To fulfill the design document requirement for manual product input functionality, allowing users to create new products directly from the UI without needing to import files.

**What**:
- Added "Manual Input" section to the Import page
- Created a comprehensive product creation form with all product fields:
  - Product ID (required)
  - Name (required)
  - Brand (optional)
  - Price (optional, defaults to 0)
  - Stock (optional, defaults to 0)
  - Order Quantity (optional, defaults to 0)
  - Image URL (optional)
  - Remarks (optional)
- Form includes validation for required fields
- Responsive design for mobile and desktop
- Form can be toggled to show/hide for better UX

### Fixed - Responsive Design Issues

**Why**: To fix responsive design problems that prevented proper mobile layout, specifically the ProductDetail page grid layout and navigation bar.

**What**:
- Fixed ProductDetail page responsive layout by adding proper CSS classes and media queries
- Improved navigation bar responsive behavior for mobile devices
- Added responsive CSS for import form (manual input section)
- Moved responsive styles from inline styles to App.css for proper media query support

### Technical Details

**Frontend Changes**:
- Updated `frontend/src/pages/Import.jsx` to include manual product creation form
- Updated `frontend/src/pages/ProductDetail.jsx` to use CSS classes for responsive design
- Updated `frontend/src/components/NavBar.jsx` to use CSS classes for responsive design
- Updated `frontend/src/App.css` with responsive media queries for mobile devices

## [1.0.0] - 2025-01-XX

### Added - Initial Implementation

**Why**: To fulfill the project requirements for a personal inventory and PO management web application as specified in project_description.md and design_doc.md.

**What**:

#### Backend (Python/FastAPI)
- Created FastAPI application with all required API endpoints
- Implemented SQLAlchemy models for Product table with all required fields
- Added database configuration supporting both PostgreSQL and SQLite
- Implemented product CRUD operations (Create, Read, Update)
- Added search functionality (by product_id, name, brand)
- Added sorting functionality (by stock, product_id)
- Implemented pagination for product lists
- Created cart endpoint to fetch products with order_qty > 0
- Implemented global reset functionality to set all stock and order_qty to 0
- Added Excel import functionality with flexible column mapping
- Added PDF import functionality (best-effort parsing)
- Implemented Pydantic schemas for request/response validation
- Added CORS middleware for frontend communication
- Created static file serving for product images

#### Frontend (React)
- Set up React application with Vite
- Implemented React Router for navigation
- Created main product list page with:
  - Product cards displaying key information
  - Search functionality with debouncing
  - Sorting options (by stock, product_id)
  - Pagination
  - Inline order quantity editing
- Created product detail page with:
  - Full product information display
  - Editable fields (stock, order_qty, remarks, name, brand, price)
  - Image display with fallback
- Created cart page showing:
  - Products with order_qty > 0
  - Total items and total cost calculation
  - Order quantity editing
- Created import page with:
  - Excel file upload and import
  - PDF file upload and import
  - Import result display with error reporting
- Implemented navigation bar with:
  - Links to all main pages
  - Cart item count badge
  - Clear All (reset) button with confirmation
- Created API client for backend communication
- Implemented CartContext for cart count management
- Added responsive design for mobile and desktop
- Implemented error handling and user feedback

#### Testing
- Created comprehensive test suite (test_core_functionality.py) covering:
  - Global reset functionality
  - Search functionality (by ID, name, brand)
  - Product detail updates
  - Inline order quantity updates
  - Validation (negative values)
  - Cart view filtering
  - Cart edit synchronization

#### Documentation
- Created README.md with:
  - Project overview
  - Setup instructions
  - Usage guide
  - API documentation
  - Troubleshooting tips
- Created CHANGELOG.md to track all changes

### Technical Details

**Backend**:
- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- Pydantic 2.5.0
- openpyxl 3.1.2 (Excel parsing)
- PyPDF2 3.0.1 (PDF parsing)

**Frontend**:
- React with Vite
- React Router DOM 7.10.1
- Axios for API calls

**Database Schema**:
- Products table with indexes on product_id, name, brand, order_qty
- Composite index on (brand, name) for search optimization

### Files Created

**Backend**:
- `backend/app/__init__.py`
- `backend/app/database.py`
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/main.py`
- `backend/app/importers.py`
- `backend/requirements.txt`
- `backend/run.py`
- `backend/.gitignore`

**Frontend**:
- `frontend/src/api.js`
- `frontend/src/App.jsx`
- `frontend/src/App.css`
- `frontend/src/components/NavBar.jsx`
- `frontend/src/components/ProductCard.jsx`
- `frontend/src/pages/ProductList.jsx`
- `frontend/src/pages/ProductDetail.jsx`
- `frontend/src/pages/Cart.jsx`
- `frontend/src/pages/Import.jsx`
- `frontend/src/contexts/CartContext.jsx`

**Testing & Documentation**:
- `test_core_functionality.py`
- `README.md`
- `CHANGELOG.md`

