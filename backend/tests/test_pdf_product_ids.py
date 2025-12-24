#!/usr/bin/env python3
"""
Test suite for PDF product ID extraction using position-based parsing.

This test validates the new position-based approach for extracting product IDs
from Chinatown Supermarket invoice PDFs. The approach uses the consistent table
structure where product IDs appear after the Amount column.

Usage:
    cd backend
    source venv/bin/activate
    python tests/test_pdf_product_ids.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.importers import (
    parse_pdf,
    _extract_product_id_and_barcode_from_tail,
    _looks_like_chinatown_summary_line,
    _parse_chinatown_summary_line,
)
from decimal import Decimal


def test_extract_product_id_and_barcode_from_tail():
    """Test the core position-based extraction function."""
    print("\n" + "=" * 70)
    print("Testing _extract_product_id_and_barcode_from_tail()")
    print("=" * 70)
    
    test_cases = [
        # (tail, expected_product_id, expected_barcode)
        ("800026 845970000267", "800026", "845970000267"),
        ("800460S", "800460S", None),
        ("GT-099 859176000518", "GT-099", "859176000518"),
        ("JE-3345 4930428833453", "JE-3345", "4930428833453"),
        ("JK51029 4945569510293", "JK51029", "4945569510293"),
        ("JKK283 4956810802753", "JKK283", "4956810802753"),
        ("JL8166 4973430017688", "JL8166", "4973430017688"),
        ("HOOK", "HOOK", None),
        ("801401P 8851130080347", "801401P", "8851130080347"),
        ("", None, None),
    ]
    
    passed = 0
    failed = 0
    
    for tail, expected_id, expected_barcode in test_cases:
        product_id, barcode = _extract_product_id_and_barcode_from_tail(tail)
        
        if product_id == expected_id and barcode == expected_barcode:
            print(f"  ✓ PASS: '{tail}' -> ({product_id}, {barcode})")
            passed += 1
        else:
            print(f"  ✗ FAIL: '{tail}'")
            print(f"    Expected: ({expected_id}, {expected_barcode})")
            print(f"    Got:      ({product_id}, {barcode})")
            failed += 1
    
    print(f"\n  Results: {passed} passed, {failed} failed")
    return failed == 0


def test_looks_like_chinatown_summary_line():
    """Test summary line detection."""
    print("\n" + "=" * 70)
    print("Testing _looks_like_chinatown_summary_line()")
    print("=" * 70)
    
    test_cases = [
        # (line, expected_result)
        ("2 PCS/CS ****4 28.00 112.00800026 845970000267", True),
        ("1 SET / CS1 130.00 130.00800460S", True),
        ("10PCS/BX, 10 BX/CS20 10.00 200.00GT-099 859176000518", True),
        ("S/S HOOK 挂钩 20 0.00 0.00HOOK", True),
        ("DACHU 18 QT  N/S COOKING POT 不粘双耳汤锅", False),  # Description line, no prices
        ("Invoice", False),
        ("Page 1", False),
        ("", False),
    ]
    
    passed = 0
    failed = 0
    
    for line, expected in test_cases:
        result = _looks_like_chinatown_summary_line(line)
        
        if result == expected:
            status = "summary" if expected else "not summary"
            print(f"  ✓ PASS: Correctly identified as {status}")
            print(f"    Line: '{line[:60]}...' " if len(line) > 60 else f"    Line: '{line}'")
            passed += 1
        else:
            status = "summary" if expected else "not summary"
            print(f"  ✗ FAIL: Should be {status}")
            print(f"    Line: '{line}'")
            failed += 1
    
    print(f"\n  Results: {passed} passed, {failed} failed")
    return failed == 0


def test_parse_chinatown_summary_line():
    """Test full summary line parsing."""
    print("\n" + "=" * 70)
    print("Testing _parse_chinatown_summary_line()")
    print("=" * 70)
    
    test_cases = [
        # (line, expected_product_id, expected_price)
        ("2 PCS/CS ****4 28.00 112.00800026 845970000267", "800026", Decimal("28.00")),
        ("1 SET / CS1 130.00 130.00800460S", "800460S", Decimal("130.00")),
        ("10PCS/BX, 10 BX/CS20 10.00 200.00GT-099 859176000518", "GT-099", Decimal("10.00")),
        ("12 PCS / BX, 288 PCS / CS72 1.50 108.00JE-3345 4930428833453", "JE-3345", Decimal("1.50")),
        ("6PCS/ BX, 60PCS/CS6 13.00 78.00JK51029 4945569510293", "JK51029", Decimal("13.00")),
        ("10 PCS /BOX, 240PCS / CS50 1.40 70.00JKK283 4956810802753", "JKK283", Decimal("1.40")),
        ("10 PCS /BOX, 180PCS / CS20 1.30 26.00JL8166 4973430017688", "JL8166", Decimal("1.30")),
        ("12 PCS/BOX, 300 PCS / CS12 1.30 15.60801401P 8851130080347", "801401P", Decimal("1.30")),
    ]
    
    passed = 0
    failed = 0
    
    for line, expected_id, expected_price in test_cases:
        result = _parse_chinatown_summary_line(line)
        
        if result is None:
            print(f"  ✗ FAIL: Parse returned None")
            print(f"    Line: '{line}'")
            failed += 1
            continue
        
        price, product_id, pack_text = result
        
        if product_id == expected_id and price == expected_price:
            print(f"  ✓ PASS: '{expected_id}' @ ${expected_price}")
            passed += 1
        else:
            print(f"  ✗ FAIL: Line: '{line[:50]}...'")
            print(f"    Expected: product_id={expected_id}, price={expected_price}")
            print(f"    Got:      product_id={product_id}, price={price}")
            failed += 1
    
    print(f"\n  Results: {passed} passed, {failed} failed")
    return failed == 0


def test_parse_pdf_with_sample_files():
    """Test full PDF parsing with the sample invoice files."""
    print("\n" + "=" * 70)
    print("Testing parse_pdf() with sample invoice files")
    print("=" * 70)
    
    # Find sample PDF files
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sample_dir = os.path.join(base_dir, "sample_data")
    
    # Also check the main project directory
    main_project_dir = "/Users/bojun/Cursor_proj/Inventory_PO_Web_App"
    alt_sample_dir = os.path.join(main_project_dir, "sample_data")
    
    if os.path.exists(sample_dir):
        pdf_dir = sample_dir
    elif os.path.exists(alt_sample_dir):
        pdf_dir = alt_sample_dir
    else:
        print(f"  ✗ Cannot find sample_data directory")
        print(f"    Tried: {sample_dir}")
        print(f"    Tried: {alt_sample_dir}")
        return False
    
    pdf_files = [
        os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith('.pdf')
    ]
    
    if not pdf_files:
        print(f"  ✗ No PDF files found in {pdf_dir}")
        return False
    
    all_passed = True
    
    # Expected product IDs for each file (sample of key IDs to verify)
    expected_ids = {
        "Chinatown Supermarket UT inv 35464.pdf": [
            "800013", "800014", "800015", "800460S", "800465S"
        ],
        "Chinatown Supermarket UT inv 36889.pdf": [
            "800026", "800027", "800460S", "GT-099", "JE-3345", 
            "JK51029", "JK51030", "JKK283", "JL8166", "HOOK",
            "801401P", "801402P"
        ],
        "chinatown_invoice_sample.pdf": [
            "800318", "800572", "800600", "800601"
        ],
    }
    
    for pdf_path in pdf_files:
        pdf_name = os.path.basename(pdf_path)
        print(f"\n  --- {pdf_name} ---")
        
        products, errors = parse_pdf(pdf_path)
        
        print(f"    Products extracted: {len(products)}")
        print(f"    Errors: {len(errors)}")
        
        if len(products) == 0:
            print(f"    ✗ FAIL: No products extracted!")
            all_passed = False
            continue
        
        # Get all extracted product IDs
        extracted_ids = {p.product_id for p in products}
        
        # Check for expected IDs
        if pdf_name in expected_ids:
            missing = []
            found = []
            for expected_id in expected_ids[pdf_name]:
                if expected_id in extracted_ids:
                    found.append(expected_id)
                else:
                    missing.append(expected_id)
            
            if missing:
                print(f"    ✗ FAIL: Missing expected product IDs: {missing}")
                all_passed = False
            else:
                print(f"    ✓ PASS: All expected product IDs found")
            
            print(f"    Verified IDs: {found}")
        
        # Show a sample of extracted products
        print(f"    Sample products:")
        for product in products[:5]:
            print(f"      - {product.product_id}: {product.name[:40]}... @ ${product.price}")
        
        # Show alphanumeric product IDs specifically
        alphanumeric_ids = [p for p in products if not p.product_id.isdigit()]
        if alphanumeric_ids:
            print(f"    Alphanumeric product IDs ({len(alphanumeric_ids)}):")
            for product in alphanumeric_ids[:10]:
                print(f"      - {product.product_id}: {product.name[:35]}...")
    
    return all_passed


def test_specific_product_ids():
    """Test that specific problematic product IDs are correctly extracted."""
    print("\n" + "=" * 70)
    print("Testing specific product ID formats")
    print("=" * 70)
    
    # Find the invoice with alphanumeric IDs
    main_project_dir = "/Users/bojun/Cursor_proj/Inventory_PO_Web_App"
    pdf_path = os.path.join(main_project_dir, "sample_data", "Chinatown Supermarket UT inv 36889.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"  ✗ Cannot find test PDF: {pdf_path}")
        return False
    
    products, errors = parse_pdf(pdf_path)
    
    # These are the specific product IDs that were problematic before
    required_ids = {
        "GT-099": "COOKING TORCH",
        "JE-3345": "JAPANESE TEA BAG",
        "JK51029": "JAPANESE SUSHI KNIFE",
        "JK51030": "JAPANESE KITCHEN KNIFE",
        "JK51031": "JAPANESE KITCHEN KNIFE",
        "JK51182": "JAPANESE KITCHEN KNIFE",
        "JKK283": "TRIANGLE ONIGIRI MOLD",
        "JL8166": "JP SUSHI ROLLER",
        "HOOK": "S/S HOOK",
        "800460S": "ALUMINUM STOCK POT",
        "801401P": "KIWI S/S KNIFE #502",
    }
    
    product_map = {p.product_id: p for p in products}
    
    passed = 0
    failed = 0
    
    for product_id, expected_name_part in required_ids.items():
        if product_id in product_map:
            product = product_map[product_id]
            if expected_name_part.lower() in product.name.lower():
                print(f"  ✓ PASS: {product_id} -> '{product.name[:50]}'")
                passed += 1
            else:
                print(f"  ✗ FAIL: {product_id} found but name doesn't match")
                print(f"    Expected to contain: '{expected_name_part}'")
                print(f"    Got: '{product.name}'")
                failed += 1
        else:
            print(f"  ✗ FAIL: {product_id} not found in extracted products")
            failed += 1
    
    print(f"\n  Results: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all tests."""
    print("=" * 70)
    print("PDF Product ID Extraction Test Suite")
    print("Position-Based Parsing Approach")
    print("=" * 70)
    
    results = []
    
    results.append(("Unit: _extract_product_id_and_barcode_from_tail", 
                   test_extract_product_id_and_barcode_from_tail()))
    results.append(("Unit: _looks_like_chinatown_summary_line", 
                   test_looks_like_chinatown_summary_line()))
    results.append(("Unit: _parse_chinatown_summary_line", 
                   test_parse_chinatown_summary_line()))
    results.append(("Integration: parse_pdf with sample files", 
                   test_parse_pdf_with_sample_files()))
    results.append(("Integration: specific product IDs", 
                   test_specific_product_ids()))
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    if all_passed:
        print("All tests PASSED!")
        return 0
    else:
        print("Some tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
