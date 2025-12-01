"""
Test suite for parse_ebc_pad_page and normalize_pad functions.
Mission 4 - Smoke and functional tests.
"""

import json
import sys
sys.path.insert(0, '.')

from data_scraper.html_scraper import parse_ebc_pad_page, normalize_pad

# Load schema for validation
with open('data_scraper/schema_pad.json', 'r') as f:
    schema = json.load(f)

def validate_against_schema(data: dict) -> bool:
    """Basic validation against schema requirements."""
    required_fields = schema.get('required', [])
    
    # Check all required fields are present
    for field in required_fields:
        if field not in data:
            print(f"[FAIL] Missing required field: {field}")
            return False
        if data[field] is None:
            print(f"[FAIL] Required field is None: {field}")
            return False
        if data[field] == "":
            print(f"[FAIL] Required field is empty string: {field}")
            return False
    
    # Check types for required numeric fields
    numeric_fields = ['length_mm', 'height_mm', 'thickness_mm']
    for field in numeric_fields:
        if not isinstance(data[field], (int, float)):
            print(f"[FAIL] {field} should be numeric, got {type(data[field])}")
            return False
    
    # Check string fields
    string_fields = ['shape_id', 'brand', 'catalog_ref']
    for field in string_fields:
        if not isinstance(data[field], str):
            print(f"[FAIL] {field} should be string, got {type(data[field])}")
            return False
    
    # Check optional fields can be None
    if data.get('swept_area_mm2') is not None:
        if not isinstance(data['swept_area_mm2'], (int, float)):
            print(f"[FAIL] swept_area_mm2 should be numeric or None, got {type(data['swept_area_mm2'])}")
            return False
    
    if data.get('backing_plate_type') is not None:
        if not isinstance(data['backing_plate_type'], str):
            print(f"[FAIL] backing_plate_type should be string or None, got {type(data['backing_plate_type'])}")
            return False
    
    return True

print("="*60)
print("MISSION 4 - PARSE_EBC_PAD_PAGE TESTS")
print("="*60)

# ============================================================
# Test 1: Smoke Test - Minimal HTML
# ============================================================
print("\n[TEST 1] Smoke Test - Minimal HTML table")
print("-" * 60)

html_smoke = """
<html>
<head><title>EBC Brake Pad DP41686R</title></head>
<body>
    <h1>EBC Redstuff Brake Pad DP41686R - Shape: FA123</h1>
    <table class="specifications">
        <tr><td>Shape ID</td><td>FA123</td></tr>
        <tr><td>Length</td><td>100.5mm</td></tr>
        <tr><td>Height</td><td>45.2mm</td></tr>
        <tr><td>Thickness</td><td>15.0mm</td></tr>
    </table>
</body>
</html>
"""

result1 = parse_ebc_pad_page(html_smoke)
print(f"Output: {json.dumps(result1, indent=2)}")

if validate_against_schema(result1):
    print("[PASS] Smoke test PASSED - Schema validation successful")
    
    # Check specific values
    checks = [
        (result1['shape_id'] == 'FA123', "Shape ID: FA123"),
        (result1['length_mm'] == 100.5, "Length: 100.5 mm"),
        (result1['height_mm'] == 45.2, "Height: 45.2 mm"),
        (result1['thickness_mm'] == 15.0, "Thickness: 15.0 mm"),
        (result1['brand'] == 'ebc', "Brand: ebc"),
        (result1['catalog_ref'] == 'DP41686R', "Catalog ref: DP41686R"),
        (result1['swept_area_mm2'] is None, "Swept area: None (optional)"),
        (result1['backing_plate_type'] is None, "Backing plate: None (optional)"),
    ]
    
    for passed, message in checks:
        if passed:
            print(f"[PASS] {message}")
        else:
            print(f"[FAIL] {message} - got {result1}")
else:
    print("[FAIL] Smoke test FAILED")

# ============================================================
# Test 2: Functional Test - Complete HTML with all fields
# ============================================================
print("\n[TEST 2] Functional Test - Complete specifications")
print("-" * 60)

html_functional = """
<html>
<head><title>Product Page</title></head>
<body>
    <h1>EBC Yellowstuff Performance Pad FA256R</h1>
    <div class="product-info">
        <span class="product-code">FA256R</span>
    </div>
    <table class="product-specifications">
        <tr><td>Shape Code</td><td>256</td></tr>
        <tr><td>Pad Length</td><td>120.0mm</td></tr>
        <tr><td>Pad Height</td><td>52.5mm</td></tr>
        <tr><td>Pad Thickness</td><td>17.5mm</td></tr>
        <tr><td>Swept Area</td><td>6300mm²</td></tr>
        <tr><td>Backing Plate Type</td><td>Steel</td></tr>
        <tr><td>Part Number</td><td>FA256R</td></tr>
    </table>
</body>
</html>
"""

result2 = parse_ebc_pad_page(html_functional)
print(f"Output: {json.dumps(result2, indent=2)}")

if validate_against_schema(result2):
    print("[PASS] Functional test PASSED - Schema validation successful")
    
    # Check all extracted values
    checks = [
        (result2['shape_id'] == '256', "Shape ID: 256"),
        (result2['length_mm'] == 120.0, "Length: 120.0 mm"),
        (result2['height_mm'] == 52.5, "Height: 52.5 mm"),
        (result2['thickness_mm'] == 17.5, "Thickness: 17.5 mm"),
        (result2['swept_area_mm2'] == 6300.0, "Swept area: 6300.0 mm²"),
        (result2['backing_plate_type'] == 'Steel', "Backing plate: Steel"),
        (result2['catalog_ref'] == 'FA256R', "Catalog ref: FA256R"),
        (result2['brand'] == 'ebc', "Brand: ebc"),
    ]
    
    for passed, message in checks:
        if passed:
            print(f"[PASS] {message}")
        else:
            print(f"[FAIL] {message}")
else:
    print("[FAIL] Functional test FAILED")

# ============================================================
# Test 3: Definition List Format
# ============================================================
print("\n[TEST 3] Alternative HTML Format - Definition List")
print("-" * 60)

html_dl = """
<html>
<body>
    <h1>EBC Greenstuff Pad DP21234</h1>
    <dl class="specifications">
        <dt>Shape</dt><dd>21234</dd>
        <dt>Length</dt><dd>95.5</dd>
        <dt>Height</dt><dd>42.0</dd>
        <dt>Thickness</dt><dd>14.5</dd>
        <dt>Reference</dt><dd>DP21234</dd>
    </dl>
</body>
</html>
"""

result3 = parse_ebc_pad_page(html_dl)
print(f"Output: {json.dumps(result3, indent=2)}")

if validate_against_schema(result3):
    print("[PASS] Definition list test PASSED - Schema validation successful")
    
    checks = [
        (result3['shape_id'] == '21234', "Shape ID: 21234"),
        (result3['length_mm'] == 95.5, "Length: 95.5 mm"),
        (result3['height_mm'] == 42.0, "Height: 42.0 mm"),
        (result3['thickness_mm'] == 14.5, "Thickness: 14.5 mm"),
        (result3['catalog_ref'] == 'DP21234', "Catalog ref: DP21234"),
    ]
    
    for passed, message in checks:
        if passed:
            print(f"[PASS] {message}")
        else:
            print(f"[FAIL] {message}")
else:
    print("[FAIL] Definition list test FAILED")

# ============================================================
# Test 4: Direct normalize_pad test
# ============================================================
print("\n[TEST 4] Direct normalize_pad function test")
print("-" * 60)

raw_data = {
    "shape_id": "TEST123",
    "length_mm": "105.5mm",
    "height_mm": "48.0",
    "thickness_mm": "16.5",
    "swept_area_mm2": "5040mm²",
    "backing_plate_type": "Aluminum",
    "catalog_ref": "DP-TEST123"
}

result4 = normalize_pad(raw_data, source="EBC")
print(f"Output: {json.dumps(result4, indent=2)}")

if validate_against_schema(result4):
    print("[PASS] Direct normalize_pad test PASSED")
    
    checks = [
        (result4['shape_id'] == 'TEST123', "Shape ID preserved"),
        (result4['length_mm'] == 105.5, "Length cleaned and converted: 105.5"),
        (result4['height_mm'] == 48.0, "Height converted: 48.0"),
        (result4['thickness_mm'] == 16.5, "Thickness converted: 16.5"),
        (result4['swept_area_mm2'] == 5040.0, "Swept area cleaned: 5040.0"),
        (result4['backing_plate_type'] == 'Aluminum', "Backing plate preserved"),
        (result4['brand'] == 'ebc', "Brand lowercased: ebc"),
        (result4['catalog_ref'] == 'DP-TEST123', "Catalog ref preserved"),
    ]
    
    for passed, message in checks:
        if passed:
            print(f"[PASS] {message}")
        else:
            print(f"[FAIL] {message}")
else:
    print("[FAIL] Direct normalize_pad test FAILED")

print("\n" + "="*60)
print("ALL TESTS COMPLETED")
print("="*60)
