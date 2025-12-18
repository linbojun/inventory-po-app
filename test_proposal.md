# Inventory PO Web App – Test Proposal

This document defines the testing strategy and example test cases for the project.

## 1. Testing Strategy

We will have three main layers of tests:

1. **Unit Tests (Backend)**
   - Test product model logic, validation, and utility functions.
   - Test import parsers (Excel/PDF) with sample files.
   - Test business rules around order_qty and stock.

2. **API Integration Tests**
   - Use a test database.
   - Hit REST endpoints and verify JSON responses and DB side effects.
   - Focus on core use cases: search, update stock, update order_qty, cart behavior, reset.

3. **End-to-End (E2E) / UI Tests**
   - Optional but recommended.
   - Use Playwright / Cypress to simulate browser usage:
     - Search and open product detail
     - Scroll main list and update order_qty
     - Use cart view
     - Use reset button

Manual exploratory testing on mobile browsers will also be done to validate responsive design and touch interactions.

---

## 2. Assumptions

- Single-user environment.
- Test database is isolated from production.
- Import templates (Excel/PDF) are stable and documented.

---

## 3. Test Cases by Feature

### 3.1 Global Reset (Clear All)

**TC-RESET-01 – Successful reset**

- Precondition:
  - At least 3 products exist with various `stock` and `order_qty` values (non-zero).
- Steps:
  1. Call `POST /api/products/reset`.
  2. Fetch all products via `GET /api/products`.
- Expected:
  - For every product: `stock == 0` and `order_qty == 0`.
  - Cart (`GET /api/cart`) returns empty list.
  - Response status for reset is 200 OK.

**TC-RESET-02 – Partial failure protection**

- Setup:
  - Simulate a DB error in the middle of reset transaction.
- Steps:
  1. Trigger reset API.
- Expected:
  - API returns an error (e.g., 500).
  - No product has changed `stock` or `order_qty` (transaction rolled back).

### 3.2 Search and Product Detail

**TC-SEARCH-01 – Search by product ID**

- Precondition:
  - Product with `product_id = "A123"` exists.
- Steps:
  1. Call `GET /api/products?search=A123`.
- Expected:
  - Response includes product with `product_id = "A123"`.
  - Does not include unrelated products.

**TC-SEARCH-02 – Search by name or brand (case-insensitive)**

- Precondition:
  - Product with `name = "Apple Case"` and `brand = "XYZ"` exists.
- Steps:
  1. Call `GET /api/products?search=apple`.
  2. Call `GET /api/products?search=xyz`.
- Expected:
  - Both requests should match the product (case-insensitive).

**TC-DETAIL-01 – Update stock and remarks via detail page**

- Precondition:
  - Product P has `stock = 10`, `remarks = null`.
- Steps:
  1. `PUT /api/products/{id}` with `stock = 8`, `remarks = "counted on 2025-12-10"`.
  2. `GET /api/products/{id}`.
- Expected:
  - `stock == 8`, `remarks == "counted on 2025-12-10"`.

### 3.3 Main List Inline Order Quantity

**TC-LIST-01 – Inline order quantity update syncs correctly**

- Precondition:
  - Product P has `order_qty = 0`.
- Steps:
  1. From main list UI, set order_qty to 5 (calls `PATCH /api/products/{id}/order-qty`).
  2. Refresh main list (GET `/api/products`).
  3. Call `GET /api/cart`.
- Expected:
  - Main list shows `order_qty = 5`.
  - Cart includes product P with `order_qty = 5`.

**TC-LIST-02 – Order quantity cannot be negative**

- Steps:
  1. Attempt to set `order_qty = -1`.
- Expected:
  - API responds with validation error (4xx).
  - DB value for `order_qty` remains unchanged.

### 3.4 Cart View

**TC-CART-01 – Cart shows only products with order_qty > 0**

- Precondition:
  - Product A: `order_qty = 0`
  - Product B: `order_qty = 3`
  - Product C: `order_qty = 1`
- Steps:
  1. Call `GET /api/cart`.
- Expected:
  - Only B and C are returned.

**TC-CART-02 – Editing order_qty from cart updates everywhere**

- Precondition:
  - Product P: `order_qty = 3`.
- Steps:
  1. From cart UI, change order_qty to 0 (PATCH API).
  2. Fetch cart.
  3. Fetch product from main list.
- Expected:
  - Cart no longer includes P.
  - Main list shows `order_qty = 0` for P.

### 3.5 Import (Excel)

**TC-IMPORT-EXCEL-01 – Basic import**

- Precondition:
  - Database empty.
  - Excel file with 3 valid product rows.
- Steps:
  1. Call `POST /api/import/excel` with the file.
- Expected:
  - Response summary: 3 created, 0 updated, 0 failed.
  - `GET /api/products` returns 3 products matching the Excel data.

**TC-IMPORT-EXCEL-02 – Upsert behavior**

- Precondition:
  - Product with `product_id = "A123"` already exists.
  - Excel contains row with the same `product_id = "A123"` but different stock/price.
- Steps:
  1. Import Excel.
- Expected:
  - Summary shows 0 created, 1 updated.
  - Product A123 now has updated stock/price.

**TC-IMPORT-EXCEL-03 – Invalid data row**

- Precondition:
  - Excel file where one row has missing `product_id`.
- Steps:
  1. Import Excel.
- Expected:
  - Summary lists that row as failed, with reason.
  - Other valid rows are created/updated successfully.

### 3.6 Import (PDF) – Optional

**TC-IMPORT-PDF-01 – Unsupported format**

- Steps:
  1. Upload a random PDF not in the supported template format.
- Expected:
  - API returns clear error such as "Unsupported PDF format".
  - No product records are created or modified.

---

## 4. UI / E2E Test Scenarios (High-Level)

These can be implemented with Playwright / Cypress scripts or as manual test scripts.

**E2E-01 – Basic flow**

1. Open main page.
2. Import sample Excel with products.
3. Search for a specific product and open detail page.
4. Update stock and order_qty, save.
5. Return to main page and verify changes.
6. Open cart and verify product appears with correct order_qty.

**E2E-02 – Mobile layout check**

1. Open the app in mobile viewport.
2. Scroll through main product list.
3. Update order_qty on several items.
4. Open cart and verify layout and data.

**E2E-03 – Reset flow**

1. Start with some products with non-zero stock and order_qty.
2. Open cart and confirm items present.
3. Click “Clear All” and confirm.
4. Verify:
   - Main list: stock and order_qty all 0.
   - Cart: empty.

---

## 5. Acceptance Criteria

The app passes acceptance if:

- All **critical** test cases above (RESET, SEARCH, DETAIL UPDATE, LIST INLINE UPDATE, CART, IMPORT EXCEL) pass.
- Manual mobile tests confirm:
  - Layout is usable.
  - No obvious UI blocking issues.
- No data consistency bugs between main list, detail, and cart in normal usage.
