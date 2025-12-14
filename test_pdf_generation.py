#!/usr/bin/env python3
"""Test script for enhanced PDF sanction letter generation"""

import sys
import os

# Add the orchestrator directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'orchestrator'))

from services.pdf_service import PDFService

def test_basic_pdf():
    """Test basic PDF generation with minimal parameters"""
    print("Test 1: Basic PDF generation...")
    service = PDFService(output_dir="backend/orchestrator/static/pdfs")
    filename = service.generate("Test User", 500000, 10.5)
    filepath = os.path.join("backend/orchestrator/static/pdfs", filename)
    
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ Basic PDF generated: {filename} ({size} bytes)")
        return True
    else:
        print(f"❌ PDF file not found: {filepath}")
        return False

def test_full_pdf():
    """Test PDF generation with all parameters"""
    print("\nTest 2: Full PDF generation with all parameters...")
    service = PDFService(output_dir="backend/orchestrator/static/pdfs")
    filename = service.generate(
        name="Aarush Luthra",
        amount=800000,
        interest=10.5,
        pan="ABCDE1000F",
        tenure=24,
        processing_fee=1.5
    )
    filepath = os.path.join("backend/orchestrator/static/pdfs", filename)
    
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ Full PDF generated: {filename} ({size} bytes)")
        print(f"   Location: {os.path.abspath(filepath)}")
        return True
    else:
        print(f"❌ PDF file not found: {filepath}")
        return False

def test_emi_calculation():
    """Test EMI calculation"""
    print("\nTest 3: EMI calculation...")
    service = PDFService()
    
    # Test case: 5 lakh loan at 10.5% for 24 months
    emi = service._calculate_emi(500000, 10.5, 24)
    expected_emi = 23145.83  # Approximate expected value
    
    if abs(emi - expected_emi) < 100:  # Allow small variance
        print(f"✅ EMI calculation correct: ₹{emi:.2f}")
        return True
    else:
        print(f"❌ EMI calculation incorrect: got ₹{emi:.2f}, expected ~₹{expected_emi:.2f}")
        return False

def test_currency_formatting():
    """Test Indian currency formatting"""
    print("\nTest 4: Currency formatting...")
    service = PDFService()
    
    tests = [
        (500000, "₹5,00,000"),
        (1000000, "₹10,00,000"),
        (50000, "₹50,000"),
        (999, "₹999"),
    ]
    
    all_passed = True
    for amount, expected in tests:
        result = service._format_currency(amount)
        if result == expected:
            print(f"✅ {amount} → {result}")
        else:
            print(f"❌ {amount} → {result} (expected {expected})")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("="*60)
    print("Enhanced PDF Sanction Letter - Test Suite")
    print("="*60)
    
    results = []
    results.append(("Basic PDF", test_basic_pdf()))
    results.append(("Full PDF", test_full_pdf()))
    results.append(("EMI Calculation", test_emi_calculation()))
    results.append(("Currency Formatting", test_currency_formatting()))
    
    print("\n" + "="*60)
    print("Test Results Summary:")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed!")
        sys.exit(1)
