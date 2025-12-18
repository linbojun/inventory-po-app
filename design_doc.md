# Inventory PO Web App – Design Doc

## 1. Overview

This document describes the system design for an inventory and PO management web app.

- Single user (myself)
- Frontend: React
- Backend: Python (FastAPI preferred)
- Database: PostgreSQL (or SQLite as an alternative)
- Images stored in filesystem / object storage, referenced by URL in DB.

---

## 2. Functional Requirements

### 2.1 Data Import

- **Excel Import**
  - Upload an Excel file in a predefined template.
  - Parse rows into product records.
  - For each row:
    - If `product_id` exists → update the existing product.
    - If `product_id` does not exist → create a new product.
- **PDF Import**
  - Optional / best-effort.
  - Support only one or two fixed PDF layouts.
  - Parse table-like content into products.
  - Non-parseable PDFs should result in a clear error.
- **Manual Input**
  - Create new products via a “New Product” form.

### 2.2 Product Browsing & Editing

- **Main Product List Page**
  - Infinite scroll or paginated list of product cards.
  - Each card shows:
    - Image
    - Product name
    - Brand (optional on card if space permits)
    - Stock
    - Order quantity
    - (Optional) remark icon/preview
  - User can edit **order_qty** inline on the card (without opening detail page).
  - Sorting options:
    - By stock (asc/desc), if same stock then by `product_id`.
    - By `product_id` (asc/desc).
  - Search bar at top:
    - Search by product ID, name, or brand (single input field).
    - Client-side debounced search that calls backend.

- **Product Detail Page**
  - Shows all fields of the product, including image and remarks.
  - Editable fields:
    - stock
    - order_qty
    - remarks
    - (Optional) price, name, brand
  - “Save” button triggers backend update.

### 2.3 Shopping Cart View

- Shows only products with `order_qty > 0`.
- Each row/card includes:
  - Image
  - Product name / brand
  - Current stock
  - Order quantity (editable)
- When order_qty is updated:
  - Changes propagate to DB and to main list.
  - If order_qty becomes 0 → product disappears from cart.
- Optional: Display total number of items and total cost (sum of `order_qty * price`).

### 2.4 Global Clear (Reset) Action

- “Clear All” button resets **all products**:
  - `stock = 0`
  - `order_qty = 0`
- Requires a confirmation dialog.
- If any error occurs, no partial reset should be committed:
  - Prefer a single SQL transaction.

---

## 3. System Architecture

### 3.1 High-Level Architecture

- **Frontend (React SPA)**
  - Routes:
    - `/` – main product list
    - `/product/:id` – product detail
    - `/cart` – shopping cart (order list)
    - `/import` – data import page (Excel/PDF)
  - State management:
    - Use React Query / SWR for data fetching and caching,
      or simple Context/Redux store that syncs with backend APIs.

- **Backend (Python + FastAPI / Flask)**
  - Responsibilities:
    - CRUD APIs for products.
    - Search / sort APIs.
    - Import handlers (Excel, PDF).
    - Global reset operation.
  - Validation:
    - Use Pydantic models (if using FastAPI) for request/response schemas.

- **Database (PostgreSQL / SQLite)**
  - Tables:
    - `products`
    - `import_jobs` (optional, to track import history)
  - Images:
    - `image_url` field in `products`.
    - Static file server or external object storage.

---

## 4. Data Model

### 4.1 Product Table

Suggested `products` table schema:

- `id` (PK, auto-increment integer)
- `product_id` (string, unique, indexed)
- `name` (string, indexed)
- `brand` (string, indexed)
- `price` (numeric(10, 2), default 0)
- `stock` (integer, default 0)
- `order_qty` (integer, default 0)
- `image_url` (string, nullable)
- `remarks` (text, nullable)
- `created_at` (timestamp with timezone, default now)
- `updated_at` (timestamp with timezone, auto-updated)

Indexes:

- Index on `product_id` (unique).
- Index on `(brand, name)` for search.
- Index on `order_qty` for efficient cart queries.

---

## 5. API Design

Base URL: `/api`

### 5.1 Product APIs

- `GET /api/products`
  - Query params:
    - `search` (optional): string applied to product_id, name, brand.
    - `sort_by` (optional): `"stock"` or `"product_id"`.
    - `sort_dir` (optional): `"asc"` or `"desc"`, default `"asc"`.
    - `page` (optional): integer, default 1.
    - `page_size` (optional): integer, default 50.
  - Returns: paginated list of products.

- `GET /api/products/{id}`
  - Returns full product details.

- `POST /api/products`
  - Create a new product (manual input).
  - Body: product fields except `id`, `created_at`, `updated_at`.

- `PUT /api/products/{id}`
  - Update product fields including `stock`, `order_qty`, `remarks`, etc.

- `PATCH /api/products/{id}/order-qty`
  - Body: `{ "order_qty": number }`
  - Used for quick updates from main list or cart.

### 5.2 Cart APIs

- `GET /api/cart`
  - Returns all products where `order_qty > 0`.

- `PATCH /api/cart/{id}`
  - Same as updating order_qty for that product.
  - If `order_qty` becomes 0, product is removed from cart result.

### 5.3 Import APIs

- `POST /api/import/excel`
  - Upload Excel file.
  - Parse and upsert products.
  - Response: summary of created/updated/failed rows.

- `POST /api/import/pdf` (optional / best-effort)
  - Upload PDF file.
  - Attempt to parse table and upsert products.
  - Response: success/failure summary.

### 5.4 Global Reset API

- `POST /api/products/reset`
  - Action: set `stock = 0` and `order_qty = 0` for all products.
  - Implementation should use a single transaction.

---

## 6. Frontend UI / UX Design

### 6.1 Main Product List

- Top bar:
  - Search input
  - Sort dropdown (Stock / Product ID)
  - Cart button with badge showing cart item count
  - “Clear All” button (possibly in a more menu or secondary position)
- Product card:
  - Image (square or 4:3)
  - Product name (one line, ellipsis)
  - Brand (small text)
  - Stock: `Stock: X`
  - Order qty: `Order: [-] [ 3 ] [+]`
  - Optional “View Details” button.

### 6.2 Product Detail Page

- Large image on top.
- Product ID, name, brand, price.
- Editable fields:
  - Stock (number input)
  - Order quantity (number input / +/-)
  - Remarks (textarea)
- Save & Back buttons.

### 6.3 Cart Page

- List all `order_qty > 0` products.
- Similar layout to main product list but focused on order quantity.
- Show total count and total price at bottom.

---

## 7. Error Handling & Validation

- Frontend validation:
  - stock >= 0
  - order_qty >= 0
  - price >= 0
- Backend validation with clear error messages.
- Excel/PDF import:
  - If any row has invalid data, include row number and reason in response.

---

## 8. Performance & Scalability

- For now, assume up to a few thousand products.
- Use pagination or infinite scroll.
- Index DB columns used in search and sorting.

---

## 9. Future Enhancements (Nice-to-have)

- Authentication (basic login).
- Multiple users / roles.
- Export purchase list to Excel/PDF.
- Per-brand or per-category filters.
