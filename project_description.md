# Inventory PO Web App – Project Description

## 1. Goal

Build a personal web app to manage product inventory and purchase order (PO) quantities.

The app should:

- Let the user **view all products** in a scrollable list (mobile + desktop).
- Let the user **search products** by product ID, name, or brand.
- Let the user **update stock and order quantities** quickly during daily work.
- Provide a **“shopping cart” style view** showing only products with `order_qty > 0`.
- Support **importing product data** from Excel / PDF / manual input.
- Support **one-click reset** of stock and order quantities to start a new purchasing cycle.

Primary user: **a single internal user** (myself). Multi-user, authentication, and complex roles are out of scope for now.

---

## 2. Core Use Cases

1. **Reset before a new purchasing cycle**
   - User clicks a “Clear All” button.
   - System sets **all products’ `stock` and `order_qty` to 0**.

2. **Search and edit details via product detail page**
   - User types a product ID / name / brand in the search bar.
   - App shows matching products.
   - User clicks one product to open its detail page.
   - On the detail page, user can:
     - Update **stock**
     - Update **order_qty**
     - Add / edit **remarks (comments)**

3. **Browse all products and edit order quantity inline**
   - On the main page, user scrolls through all products (infinite scroll or pagination).
   - Each product card shows at least:
     - Product image
     - Product name
     - Current stock
     - Current order quantity
     - (Optional) snippet of remarks
   - User can update **order_qty directly on the main page** without entering the detail page.

4. **Shopping cart view**
   - User opens the “Cart / PO” view.
   - Page shows all products where `order_qty > 0`, including:
     - Product image
     - Product name / brand
     - Current stock
     - Current order quantity
   - User can also modify **order_qty** in this view.
   - When order_qty becomes 0, that product disappears from the cart.

---

## 3. Data Model (High level)

Each product record includes:

- `id` (internal database primary key)
- `product_id` (string, business ID, unique)
- `name` (string)
- `brand` (string)
- `price` (decimal)
- `stock` (integer, current inventory)
- `order_qty` (integer, planned purchase quantity)
- `image_url` (string, URL/path to product image)
- `remarks` (text, optional)
- `created_at`, `updated_at` (timestamps)

---

## 4. Platforms & Technology Preferences

- **Frontend:** React (SPA), responsive for mobile and desktop browsers.
- **Backend:** Python (FastAPI or Flask preferred).
- **Database:** 
  - Use **PostgreSQL** for production-like setup (or SQLite for very simple local use).
  - Store images as files (local or object storage like S3); save only `image_url` in DB.
- **APIs:** JSON-based REST API between frontend and backend.

---

## 5. Non-Goals (for now)

- No multi-user / login system.
- No complex role-based permissions.
- No advanced analytics or reporting.
- No third-party integrations (e.g., ERP) in the first version.

---

## 6. Definition of Done (High level)

The project is “done” when:

- The four core use cases above can be completed smoothly without manual DB operations.
- The app works well on both **mobile** and **desktop** browsers.
- Data is persisted in the database (survives browser refresh).
- Basic input validation and error feedback are implemented.
