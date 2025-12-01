"""
Test suite for parse_dba_rotor_page function.
Mission 3 - Smoke and functional tests.
"""

import json
import sys
sys.path.insert(0, '.')

from data_scraper.html_scraper import parse_dba_rotor_page

# Load schema for validation
with open('data_scraper/schema_rotor.json', 'r') as f:
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
    
    # Check types for required numeric fields
    numeric_fields = ['outer_diameter_mm', 'nominal_thickness_mm', 'hat_height_mm',
                      'overall_height_mm', 'center_bore_mm', 'bolt_circle_mm']
    for field in numeric_fields:
        if not isinstance(data[field], (int, float)):
            print(f"[FAIL] {field} should be numeric, got {type(data[field])}")
            return False
    
    # Check bolt_hole_count is int
    if not isinstance(data['bolt_hole_count'], int):
        print(f"[FAIL] bolt_hole_count should be int, got {type(data['bolt_hole_count'])}")
        return False
    
    # Check enum values
    if data['ventilation_type'] not in schema['properties']['ventilation_type']['enum']:
        print(f"[FAIL] Invalid ventilation_type: {data['ventilation_type']}")
        return False
    
    if data['directionality'] not in schema['properties']['directionality']['enum']:
        print(f"[FAIL] Invalid directionality: {data['directionality']}")
        return False
    
    return True

print("="*60)
print("MISSION 3 - PARSE_DBA_ROTOR_PAGE TESTS")
print("="*60)

# ============================================================
# Test 1: Smoke Test - Minimal HTML
# ============================================================
print("\n[TEST 1] Smoke Test - Minimal HTML table")
print("-" * 60)

html_smoke = """
<html>
<head><title>DBA Rotor DBA42134S</title></head>
<body>
    <h1>DBA 4000 Series T3 Slotted Rotor DBA42134S</h1>
    <table class="specifications">
        <tr><td>Outer Diameter</td><td>330mm</td></tr>
        <tr><td>Nominal Thickness</td><td>28mm</td></tr>
        <tr><td>Hat Height</td><td>46mm</td></tr>
        <tr><td>Overall Height</td><td>52mm</td></tr>
        <tr><td>Center Bore</td><td>64.1mm</td></tr>
        <tr><td>PCD</td><td>114.3mm</td></tr>
        <tr><td>Bolt Holes</td><td>5</td></tr>
    </table>
</body>
</html>
"""

result1 = parse_dba_rotor_page(html_smoke)
print(f"Output: {json.dumps(result1, indent=2)}")

if validate_against_schema(result1):
    print("[PASS] Smoke test PASSED - Schema validation successful")
    
    # Check specific values
    if result1['outer_diameter_mm'] == 330.0:
        print("[PASS] Outer diameter correct: 330.0 mm")
    else:
        print(f"[FAIL] Outer diameter wrong: {result1['outer_diameter_mm']}")
    
    # Check offset calculation
    expected_offset = 52.0 - 46.0
    if result1['offset_mm'] == expected_offset:
        print(f"[PASS] Offset auto-calculated: {expected_offset} mm")
    else:
        print(f"[FAIL] Offset wrong: expected {expected_offset}, got {result1['offset_mm']}")
    
    # Check ref extraction from title
    if result1['catalog_ref'] == 'DBA42134S':
        print("[PASS] Catalog ref extracted from title: DBA42134S")
    else:
        print(f"[FAIL] Catalog ref wrong: {result1['catalog_ref']}")
    
    # Check ventilation type inferred from title
    if result1['ventilation_type'] == 'slotted':
        print("[PASS] Ventilation type inferred from title: slotted")
    else:
        print(f"[INFO] Ventilation type: {result1['ventilation_type']}")
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
    <h1>DBA 5000 Series Drilled and Slotted Rotor DBA52930XD</h1>
    <div class="product-info">
        <span class="product-code">DBA52930XD</span>
    </div>
    <table class="product-specifications">
        <tr><td>Outer Diameter</td><td>355mm</td></tr>
        <tr><td>Nominal Thickness</td><td>32mm</td></tr>
        <tr><td>Hat Height</td><td>50.5mm</td></tr>
        <tr><td>Overall Height</td><td>57.0mm</td></tr>
        <tr><td>Centre Bore</td><td>70.3mm</td></tr>
        <tr><td>Bolt Circle Diameter (PCD)</td><td>120mm</td></tr>
        <tr><td>Bolt Hole Count</td><td>5</td></tr>
        <tr><td>Ventilation Type</td><td>Drilled/Slotted</td></tr>
        <tr><td>Directionality</td><td>Left</td></tr>
        <tr><td>Rotor Weight</td><td>8.2</td></tr>
        <tr><td>Mounting Type</td><td>2-piece bolted</td></tr>
        <tr><td>Offset</td><td>6.5mm</td></tr>
    </table>
</body>
</html>
"""

result2 = parse_dba_rotor_page(html_functional)
print(f"Output: {json.dumps(result2, indent=2)}")

if validate_against_schema(result2):
    print("[PASS] Functional test PASSED - Schema validation successful")
    
    # Check all extracted values
    checks = [
        (result2['outer_diameter_mm'] == 355.0, "Outer diameter: 355.0 mm"),
        (result2['nominal_thickness_mm'] == 32.0, "Nominal thickness: 32.0 mm"),
        (result2['hat_height_mm'] == 50.5, "Hat height: 50.5 mm"),
        (result2['overall_height_mm'] == 57.0, "Overall height: 57.0 mm"),
        (result2['center_bore_mm'] == 70.3, "Center bore: 70.3 mm"),
        (result2['bolt_circle_mm'] == 120.0, "Bolt circle: 120.0 mm"),
        (result2['bolt_hole_count'] == 5, "Bolt holes: 5"),
        (result2['ventilation_type'] == 'drilled_slotted', "Ventilation: drilled_slotted"),
        (result2['directionality'] == 'left', "Directionality: left"),
        (result2['offset_mm'] == 6.5, "Offset: 6.5 mm (explicit)"),
        (result2['rotor_weight_kg'] == 8.2, "Weight: 8.2 kg"),
        (result2['mounting_type'] == '2_piece_bolted', "Mounting: 2_piece_bolted"),
        (result2['catalog_ref'] == 'DBA52930XD', "Catalog ref: DBA52930XD"),
        (result2['brand'] == 'dba', "Brand: dba"),
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
    <h1>DBA 3000 Vented Rotor DBA30255</h1>
    <dl class="specifications">
        <dt>Diameter</dt><dd>280mm</dd>
        <dt>Thickness</dt><dd>22mm</dd>
        <dt>Hat Height</dt><dd>40mm</dd>
        <dt>Overall Height</dt><dd>44mm</dd>
        <dt>Centre Bore</dt><dd>65.1mm</dd>
        <dt>PCD</dt><dd>100mm</dd>
        <dt>Bolt Holes</dt><dd>4</dd>
        <dt>Part Number</dt><dd>DBA30255</dd>
    </dl>
</body>
</html>
"""

result3 = parse_dba_rotor_page(html_dl)
print(f"Output: {json.dumps(result3, indent=2)}")

if validate_against_schema(result3):
    print("[PASS] Definition list test PASSED - Schema validation successful")
    
    # Check offset calculation
    expected_offset = 44.0 - 40.0
    if result3['offset_mm'] == expected_offset:
        print(f"[PASS] Offset auto-calculated: {expected_offset} mm")
    else:
        print(f"[FAIL] Offset calculation wrong")
    
    # Check ref from dl
    if result3['catalog_ref'] == 'DBA30255':
        print("[PASS] Catalog ref from definition list: DBA30255")
    else:
        print(f"[FAIL] Catalog ref: {result3['catalog_ref']}")
else:
    print("[FAIL] Definition list test FAILED")

print("\n" + "="*60)
print("ALL TESTS COMPLETED")
print("="*60)
