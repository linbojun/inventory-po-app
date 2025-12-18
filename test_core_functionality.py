#!/usr/bin/env python3
"""
Test program for core functionality of Inventory PO Web App
This script tests the critical use cases defined in test_proposal.md
"""

import base64
import json
import time
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional

import requests

API_BASE_URL = "http://localhost:8000/api"
TEST_PRODUCT_IDS = [
    "TEST-RESET-01",
    "TEST-RESET-02",
    "TEST-SEARCH-ABC",
    "TEST-DETAIL-01",
    "TEST-LIST-01",
    "TEST-VALID-01",
    "TEST-CART-01",
    "TEST-CART-02",
    "TEST-CART-03",
    "TEST-CART-SYNC",
    "TEST-IMG-DEDUP-1",
    "TEST-IMG-DEDUP-2",
    "TEST-IMG-DEDUP-3",
    "TEST-IMG-PAD-1",
    "TEST-IMG-PAD-2",
]

PROJECT_ROOT = Path(__file__).resolve().parent

PDF_SAMPLE_PRODUCTS = [
    (
        "800318",
        "DACHU 32CM NON STICK WOK W/LID - INDUCTION 电磁炉不沾带盖炒锅 **4 PCS / CS**",
        Decimal("16.20"),
    ),
    (
        "800572",
        "ES GLASS JAR - 7L 玻璃泡菜罐 - 中号 4 PCS / CS",
        Decimal("15.00"),
    ),
    (
        "800600",
        "8' CERAMIC CASSEROLE (#2)- 1800ML 康舒耐热煲 8 PCS / CS",
        Decimal("8.50"),
    ),
    (
        "800601",
        "9' CERAMIC CASSEROLE (#1) -2400ML 康舒耐热煲 8 PCS / CS",
        Decimal("9.50"),
    ),
]

PATTERN_A_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAEklEQVR4nGP4z8DAAMIM/4EAAB/uBfsL2WiLAAAAAElFTkSuQmCC"
PATTERN_B_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAE0lEQVR4nGNgYPgPBAz/GYAMBgAt4AX7R5TYiQAAAABJRU5ErkJggg=="

class TestRunner:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.test_results = []
        self.created_product_ids = set()
    
    def log(self, message: str, status: str = "INFO"):
        """Log test messages"""
        status_symbol = {
            "PASS": "✓",
            "FAIL": "✗",
            "INFO": "ℹ",
            "WARN": "⚠"
        }.get(status, "ℹ")
        print(f"{status_symbol} {message}")
    
    def test(self, name: str, func):
        """Run a test and record results"""
        self.log(f"Running: {name}", "INFO")
        try:
            result = func()
            if result:
                self.test_results.append((name, True, None))
                self.log(f"PASS: {name}", "PASS")
                return True
            else:
                self.test_results.append((name, False, "Test returned False"))
                self.log(f"FAIL: {name}", "FAIL")
                return False
        except Exception as e:
            self.test_results.append((name, False, str(e)))
            self.log(f"FAIL: {name} - {str(e)}", "FAIL")
            return False
    
    def create_test_product(
        self,
        product_id: str,
        name: str,
        stock: int = 10,
        order_qty: int = 0,
        brand: Optional[str] = "TestBrand",
    ) -> Optional[Dict]:
        """Create a test product"""
        try:
            data = {
                "product_id": product_id,
                "name": name,
                "brand": brand or "TestBrand",
                "price": 19.99,
                "stock": stock,
                "order_qty": order_qty,
                "remarks": None
            }
            response = requests.post(f"{self.base_url}/products", data=data)
            if response.status_code == 201:
                self.created_product_ids.add(product_id)
                return response.json()
            elif response.status_code == 400:
                # Product might already exist, try to get it and align values
                products = requests.get(f"{self.base_url}/products?search={product_id}").json()
                if products.get("items"):
                    existing = products["items"][0]
                    update_payload = {
                        "name": name,
                        "brand": brand or existing.get("brand") or "TestBrand",
                        "price": data["price"],
                        "stock": stock,
                        "order_qty": order_qty,
                    }
                    if data["remarks"] is not None:
                        update_payload["remarks"] = data["remarks"]
                    requests.put(f"{self.base_url}/products/{existing['id']}", data=update_payload)
                    self.created_product_ids.add(product_id)
                    return self.get_product_by_id(existing["id"])
            return None
        except Exception as e:
            self.log(f"Error creating product: {e}", "WARN")
            return None
    
    def create_product_with_image(
        self,
        product_id: str,
        name: str,
        image_bytes: bytes,
        brand: Optional[str] = "TestBrand",
    ) -> Optional[Dict]:
        """Create a product that includes an image upload."""
        data = {
            "product_id": product_id,
            "name": name,
            "brand": brand or "TestBrand",
            "price": 9.99,
            "stock": 5,
            "order_qty": 0,
        }
        files = {
            "image": (f"{product_id}.png", image_bytes, "image/png")
        }
        try:
            response = requests.post(f"{self.base_url}/products", data=data, files=files)
        except Exception as exc:
            self.log(f"Error uploading product image: {exc}", "WARN")
            return None
        if response.status_code == 201:
            self.created_product_ids.add(product_id)
            return response.json()
        self.log(f"Image upload failed for {product_id}: {response.text}", "WARN")
        return None

    def load_fixture_image(self, relative_path: str) -> Optional[bytes]:
        """Load image bytes from repository fixtures."""
        path = PROJECT_ROOT / relative_path
        if not path.exists():
            self.log(f"Fixture not found: {path}", "WARN")
            return None
        try:
            return path.read_bytes()
        except Exception as exc:
            self.log(f"Unable to read fixture {path}: {exc}", "WARN")
            return None

    def get_product_by_id(self, db_id: int) -> Optional[Dict]:
        """Get product by database ID"""
        try:
            response = requests.get(f"{self.base_url}/products/{db_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            self.log(f"Error getting product: {e}", "WARN")
            return None

    def _put_multipart(self, url: str, fields: Dict[str, Optional[str]]):
        """Send multipart/form-data payloads, preserving empty strings."""
        boundary = f"Boundary{uuid.uuid4().hex}"
        lines = []
        for key, value in fields.items():
            lines.append(f"--{boundary}")
            lines.append(f'Content-Disposition: form-data; name="{key}"')
            lines.append("")
            lines.append("" if value is None else str(value))
        lines.append(f"--{boundary}--")
        body = "\r\n".join(lines) + "\r\n"
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        return requests.put(url, data=body.encode("utf-8"), headers=headers)
    
    def test_reset_all(self):
        """TC-RESET-01: Test global reset functionality"""
        # Create test products with non-zero values
        p1 = self.create_test_product("TEST-RESET-01", "Reset Test 1", stock=5, order_qty=3)
        p2 = self.create_test_product("TEST-RESET-02", "Reset Test 2", stock=10, order_qty=7)
        
        if not p1 or not p2:
            return False
        
        # Reset all products
        response = requests.post(f"{self.base_url}/products/reset")
        if response.status_code != 200:
            return False
        
        # Verify all products are reset
        p1_after = self.get_product_by_id(p1["id"])
        p2_after = self.get_product_by_id(p2["id"])
        
        if not p1_after or not p2_after:
            return False
        
        # Check cart is empty
        cart_response = requests.get(f"{self.base_url}/cart")
        cart = cart_response.json()
        
        return (p1_after["stock"] == 0 and p1_after["order_qty"] == 0 and
                p2_after["stock"] == 0 and p2_after["order_qty"] == 0 and
                cart.get("total", 0) == 0)
    
    def test_search(self):
        """TC-SEARCH-01, TC-SEARCH-02: Test search functionality"""
        # Create test product
        product = self.create_test_product("TEST-SEARCH-ABC", "Apple Case", brand="XYZ Brand")
        if not product:
            return False
        
        # Search by product ID
        response = requests.get(f"{self.base_url}/products?search=TEST-SEARCH-ABC")
        if response.status_code != 200:
            return False
        results = response.json()
        found = any(p["product_id"] == "TEST-SEARCH-ABC" for p in results.get("items", []))
        if not found:
            return False
        
        # Search by name (case-insensitive)
        response = requests.get(f"{self.base_url}/products?search=apple")
        if response.status_code != 200:
            return False
        results = response.json()
        found = any("apple" in p["name"].lower() for p in results.get("items", []))
        if not found:
            return False
        
        # Search by brand (case-insensitive)
        response = requests.get(f"{self.base_url}/products?search=xyz")
        if response.status_code != 200:
            return False
        results = response.json()
        found = any("xyz" in (p.get("brand") or "").lower() for p in results.get("items", []))
        
        return found
    
    def test_product_detail_update(self):
        """TC-DETAIL-01: Test updating product via detail page"""
        product = self.create_test_product("TEST-DETAIL-01", "Detail Test", stock=10, order_qty=0)
        if not product:
            return False
        
        # Update stock and remarks
        update_data = {
            "stock": 8,
            "remarks": "counted on 2025-12-10"
        }
        response = requests.put(f"{self.base_url}/products/{product['id']}", data=update_data)
        if response.status_code != 200:
            return False
        
        # Verify update
        updated = self.get_product_by_id(product["id"])
        if not updated:
            return False
        
        if not (updated["stock"] == 8 and updated["remarks"] == "counted on 2025-12-10"):
            return False

        # Clear remarks (set to empty string should store as null)
        response = self._put_multipart(
            f"{self.base_url}/products/{product['id']}",
            {"name": updated["name"], "remarks": ""}
        )
        if response.status_code != 200:
            return False
        cleared = self.get_product_by_id(product["id"])
        return cleared is not None and cleared["remarks"] is None
    
    def test_inline_order_qty_update(self):
        """TC-LIST-01: Test inline order quantity update"""
        product = self.create_test_product("TEST-LIST-01", "List Test", stock=5, order_qty=0)
        if not product:
            return False
        
        # Update order_qty via PATCH
        response = requests.patch(
            f"{self.base_url}/products/{product['id']}/order-qty",
            json={"order_qty": 5}
        )
        if response.status_code != 200:
            return False
        
        # Verify in main list
        response = requests.get(f"{self.base_url}/products?search=TEST-LIST-01")
        results = response.json()
        found_product = next((p for p in results.get("items", []) if p["product_id"] == "TEST-LIST-01"), None)
        if not found_product or found_product["order_qty"] != 5:
            return False
        
        # Verify in cart
        cart_response = requests.get(f"{self.base_url}/cart")
        cart = cart_response.json()
        cart_product = next((p for p in cart.get("items", []) if p["product_id"] == "TEST-LIST-01"), None)
        
        return cart_product is not None and cart_product["order_qty"] == 5
    
    def test_order_qty_validation(self):
        """TC-LIST-02: Test order quantity cannot be negative"""
        product = self.create_test_product("TEST-VALID-01", "Validation Test", stock=5, order_qty=0)
        if not product:
            return False
        
        # Try to set negative order_qty
        response = requests.patch(
            f"{self.base_url}/products/{product['id']}/order-qty",
            json={"order_qty": -1}
        )
        # Should return 422 (validation error) or 400
        if response.status_code not in [400, 422]:
            return False
        
        # Verify value unchanged
        updated = self.get_product_by_id(product["id"])
        return updated and updated["order_qty"] == 0
    
    def test_cart_view(self):
        """TC-CART-01: Test cart shows only products with order_qty > 0"""
        # Create products with different order_qty
        p1 = self.create_test_product("TEST-CART-01", "Cart Test 1", stock=5, order_qty=0)
        p2 = self.create_test_product("TEST-CART-02", "Cart Test 2", stock=5, order_qty=3)
        p3 = self.create_test_product("TEST-CART-03", "Cart Test 3", stock=5, order_qty=1)
        
        if not p1 or not p2 or not p3:
            return False
        
        # Get cart
        response = requests.get(f"{self.base_url}/cart")
        if response.status_code != 200:
            return False
        
        cart = response.json()
        items = cart.get("items", [])
        product_ids = [p["product_id"] for p in items]
        
        # p1 should NOT be in cart (order_qty = 0)
        # p2 and p3 SHOULD be in cart (order_qty > 0)
        return ("TEST-CART-01" not in product_ids and
                "TEST-CART-02" in product_ids and
                "TEST-CART-03" in product_ids)
    
    def test_cart_edit_sync(self):
        """TC-CART-02: Test editing order_qty from cart updates everywhere"""
        product = self.create_test_product("TEST-CART-SYNC", "Cart Sync Test", stock=5, order_qty=3)
        if not product:
            return False
        
        # Update order_qty to 0 from cart
        response = requests.patch(
            f"{self.base_url}/products/{product['id']}/order-qty",
            json={"order_qty": 0}
        )
        if response.status_code != 200:
            return False
        
        # Verify cart no longer includes product
        cart_response = requests.get(f"{self.base_url}/cart")
        cart = cart_response.json()
        product_ids = [p["product_id"] for p in cart.get("items", [])]
        if "TEST-CART-SYNC" in product_ids:
            return False
        
        # Verify main list shows order_qty = 0
        list_response = requests.get(f"{self.base_url}/products?search=TEST-CART-SYNC")
        results = list_response.json()
        found_product = next((p for p in results.get("items", []) if p["product_id"] == "TEST-CART-SYNC"), None)
        
        return found_product is not None and found_product["order_qty"] == 0

    def test_pdf_import(self):
        """TC-IMPORT-PDF: Validate Chinatown invoice PDF import mapping"""
        pdf_path = Path(__file__).resolve().parent / "sample_data" / "chinatown_invoice_sample.pdf"
        if not pdf_path.exists():
            self.log(f"Sample PDF not found at {pdf_path}", "FAIL")
            return False
        
        # Ensure sample product ids don't conflict with existing data
        for product_id, _, _ in PDF_SAMPLE_PRODUCTS:
            self._delete_product_by_product_id(product_id)
        
        try:
            with pdf_path.open("rb") as pdf_file:
                response = requests.post(
                    f"{self.base_url}/import/pdf",
                    files={"file": (pdf_path.name, pdf_file, "application/pdf")}
                )
        except Exception as exc:
            self.log(f"Error uploading PDF: {exc}", "WARN")
            return False
        
        if response.status_code != 200:
            self.log(f"PDF import failed: {response.text}", "WARN")
            return False
        
        try:
            summary = response.json()
        except ValueError as exc:
            self.log(f"Invalid JSON response from PDF import: {exc}", "WARN")
            return False
        
        imported_count = summary.get("created", 0) + summary.get("updated", 0)
        if imported_count < len(PDF_SAMPLE_PRODUCTS):
            self.log(f"Expected {len(PDF_SAMPLE_PRODUCTS)} products, got {imported_count}", "WARN")
            return False
        
        if "skipped_existing" not in summary:
            self.log("API response missing skipped_existing field", "WARN")
            return False
        
        self.created_product_ids.update(pid for pid, _, _ in PDF_SAMPLE_PRODUCTS)
        
        for product_id, expected_name, expected_price in PDF_SAMPLE_PRODUCTS:
            result = requests.get(f"{self.base_url}/products?search={product_id}")
            if result.status_code != 200:
                return False
            data = result.json()
            match = next((item for item in data.get("items", []) if item.get("product_id") == product_id), None)
            if not match:
                return False
            if match.get("name") != expected_name:
                return False
            price_raw = match.get("price")
            if price_raw is None:
                return False
            try:
                price_value = Decimal(str(price_raw)).quantize(Decimal("0.01"))
            except Exception:
                return False
            if price_value != expected_price:
                return False
        
        # Run import again to ensure duplicates are skipped and reported
        try:
            with pdf_path.open("rb") as pdf_file:
                duplicate_response = requests.post(
                    f"{self.base_url}/import/pdf",
                    files={"file": (pdf_path.name, pdf_file, "application/pdf")}
                )
        except Exception as exc:
            self.log(f"Error uploading PDF for duplicate test: {exc}", "WARN")
            return False
        
        if duplicate_response.status_code != 200:
            self.log(f"Duplicate PDF import failed: {duplicate_response.text}", "WARN")
            return False
        
        try:
            duplicate_summary = duplicate_response.json()
        except ValueError as exc:
            self.log(f"Invalid JSON response from duplicate PDF import: {exc}", "WARN")
            return False
        expected_ids = {pid for pid, _, _ in PDF_SAMPLE_PRODUCTS}
        skipped_items = duplicate_summary.get("skipped_existing", [])
        if not isinstance(skipped_items, list):
            self.log("skipped_existing is not a list in duplicate summary", "WARN")
            return False
        for item in skipped_items:
            product_id = item.get("product_id")
            if product_id:
                self.created_product_ids.add(product_id)
        skipped_ids = {item.get("product_id") for item in skipped_items}
        
        if not expected_ids.issubset(skipped_ids):
            self.log(
                f"Skipped IDs mismatch. Expected subset {expected_ids}, got {skipped_ids}",
                "WARN"
            )
            return False
        
        if duplicate_summary.get("created") != 0 or duplicate_summary.get("updated") != 0:
            self.log("Duplicate import should not create or update products", "WARN")
            return False
        
        if duplicate_summary.get("failed", 0) != 0:
            self.log("Duplicate import should not fail when skipping existing products", "WARN")
            return False
        
        return True

    def test_image_deduplication(self):
        """TC-IMAGE-01: Ensure similar uploads reuse existing images."""
        product_ids = ["TEST-IMG-DEDUP-1", "TEST-IMG-DEDUP-2", "TEST-IMG-DEDUP-3"]
        for product_id in product_ids:
            self._delete_product_by_product_id(product_id)
        
        primary_bytes = base64.b64decode(PATTERN_A_BASE64)
        alternate_bytes = base64.b64decode(PATTERN_B_BASE64)
        
        first = self.create_product_with_image(product_ids[0], "Image Dedup 1", primary_bytes)
        second = self.create_product_with_image(product_ids[1], "Image Dedup 2", primary_bytes)
        third = self.create_product_with_image(product_ids[2], "Image Dedup 3", alternate_bytes)
        
        if not first or not second or not third:
            return False
        
        first_url = first.get("image_url")
        second_url = second.get("image_url")
        third_url = third.get("image_url")
        
        if not first_url or not second_url or not third_url:
            return False
        
        return first_url == second_url and third_url != first_url

    def test_image_deduplication_with_padding(self):
        """TC-IMAGE-02: Ensure padded vs. cropped photos reuse the same file."""
        product_ids = ["TEST-IMG-PAD-1", "TEST-IMG-PAD-2"]
        for product_id in product_ids:
            self._delete_product_by_product_id(product_id)

        padded_bytes = self.load_fixture_image("backend/static/images/800000_23ae6915.png")
        trimmed_bytes = self.load_fixture_image("backend/static/images/test_01_535f18cb.png")
        if not padded_bytes or not trimmed_bytes:
            return False

        first = self.create_product_with_image(product_ids[0], "Image Dedup Padded", padded_bytes)
        second = self.create_product_with_image(product_ids[1], "Image Dedup Trimmed", trimmed_bytes)
        if not first or not second:
            return False

        first_url = first.get("image_url")
        second_url = second.get("image_url")
        if not first_url or not second_url:
            return False

        return first_url == second_url

    def _delete_product_by_product_id(self, product_id: str):
        """Delete a product by its product_id if it exists (used for cleanup)."""
        try:
            response = requests.get(f"{self.base_url}/products?search={product_id}")
            if response.status_code != 200:
                return
            data = response.json()
            for item in data.get("items", []):
                if item.get("product_id", "").lower() == product_id.lower():
                    requests.delete(f"{self.base_url}/products/{item['id']}")
        except Exception as e:
            self.log(f"Error cleaning product {product_id}: {e}", "WARN")

    def cleanup_all_test_products(self):
        """Remove any products created during tests or left over from previous runs."""
        targets = set(TEST_PRODUCT_IDS) | set(self.created_product_ids)
        for product_id in targets:
            self._delete_product_by_product_id(product_id)
        self.created_product_ids.clear()

    def run_all_tests(self):
        """Run all test cases"""
        print("\n" + "="*60)
        print("Inventory PO Web App - Core Functionality Tests")
        print("="*60 + "\n")
        
        # Check if API is available
        try:
            response = requests.get(f"{self.base_url.replace('/api', '')}")
            self.log("API server is reachable", "INFO")
        except Exception as e:
            self.log(f"API server is not reachable: {e}", "FAIL")
            self.log("Please make sure the backend server is running on http://localhost:8000", "WARN")
            return

        # Ensure a clean slate before running tests
        self.cleanup_all_test_products()

        try:
            # Run tests
            tests = [
                ("Global Reset", self.test_reset_all),
                ("Search Functionality", self.test_search),
                ("Product Detail Update", self.test_product_detail_update),
                ("Inline Order Qty Update", self.test_inline_order_qty_update),
                ("Order Qty Validation", self.test_order_qty_validation),
                ("Cart View", self.test_cart_view),
                ("Cart Edit Sync", self.test_cart_edit_sync),
                ("Image Similarity Deduplication", self.test_image_deduplication),
                ("Image Deduplication With Padding", self.test_image_deduplication_with_padding),
                ("PDF Import (Chinatown)", self.test_pdf_import),
            ]
            
            passed = 0
            failed = 0
            
            for test_name, test_func in tests:
                if self.test(test_name, test_func):
                    passed += 1
                else:
                    failed += 1
                time.sleep(0.5)  # Small delay between tests
            
            # Summary
            print("\n" + "="*60)
            print("Test Summary")
            print("="*60)
            print(f"Total Tests: {len(tests)}")
            print(f"Passed: {passed}")
            print(f"Failed: {failed}")
            print("="*60 + "\n")
            
            if failed == 0:
                print("✓ All tests passed! Core functionality is working correctly.")
            else:
                print("✗ Some tests failed. Please review the errors above.")
            
            return failed == 0
        finally:
            self.cleanup_all_test_products()

if __name__ == "__main__":
    runner = TestRunner()
    success = runner.run_all_tests()
    exit(0 if success else 1)

