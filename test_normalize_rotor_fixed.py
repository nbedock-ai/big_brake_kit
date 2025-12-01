"""
Test suite for normalize_rotor function.
Mission 2 - Smoke and functional tests.
"""

import json
import sys
sys.path.insert(0, '.')

from data_scraper.html_scraper import normalize_rotor

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
        print(f"❌ Invalid ventilation_type: {data['ventilation_type']}")
        return False
    
    if data['directionality'] not in schema['properties']['directionality']['enum']:
        print(f"[FAIL] Invalid directionality: {data['directionality']}")
        return False
    
    return True

print("="*60)
print("MISSION 2 - NORMALIZE_ROTOR TESTS")
print("="*60)

# ============================================================
# Test 1: Smoke Test (from workflow)
# ============================================================
print("\n[TEST 1] Smoke Test")
print("-" * 60)

sample1 = {
    "outer_diameter_mm": "330",
    "nominal_thickness_mm": "28",
    "hat_height_mm": "46",
    "overall_height_mm": "52",
    "center_bore_mm": "64.1",
    "bolt_circle_mm": "114.3",
    "bolt_hole_count": "5",
    "ventilation_type": "vented",
    "directionality": "non_directional",
    "ref": "TEST123"
}

result1 = normalize_rotor(sample1, "dba")
print(f"Input: {sample1}")
print(f"Output: {json.dumps(result1, indent=2)}")

# Validate
if validate_against_schema(result1):
    print("[PASS] Smoke test PASSED - Schema validation successful")
    
    # Check offset calculation
    expected_offset = 52.0 - 46.0
    if result1['offset_mm'] == expected_offset:
        print(f"[PASS] Offset calculation correct: {expected_offset} mm")
    else:
        print(f"[FAIL] Offset calculation wrong: expected {expected_offset}, got {result1['offset_mm']}")
else:
    print("❌ Smoke test FAILED")

# ============================================================
# Test 2: Functional Test - Drilled/Slotted with explicit offset
# ============================================================
print("\n[TEST 2] Functional Test - Drilled/Slotted with explicit offset")
print("-" * 60)

sample2 = {
    "outer_diameter_mm": "355",
    "nominal_thickness_mm": "32",
    "hat_height_mm": "50.5",
    "overall_height_mm": "57.0",
    "center_bore_mm": "70.3",
    "bolt_circle_mm": "120",
    "bolt_hole_count": "5",
    "ventilation_type": "drilled/slotted",
    "directionality": "left",
    "offset_mm": "6.5",
    "rotor_weight_kg": "8.2",
    "mounting_type": "2_piece_bolted",
    "ref": "DBA4930XS"
}

result2 = normalize_rotor(sample2, "dba")
print(f"Input: {sample2}")
print(f"Output: {json.dumps(result2, indent=2)}")

if validate_against_schema(result2):
    print("[PASS] Functional test 2 PASSED - Schema validation successful")
    
    # Check specific transformations
    if result2['ventilation_type'] == 'drilled_slotted':
        print("✅ Ventilation type correctly standardized: drilled_slotted")
    else:
        print(f"[FAIL] Ventilation type wrong: {result2['ventilation_type']}")
    
    if result2['directionality'] == 'left':
        print("[PASS] Directionality preserved: left")
    else:
        print(f"[FAIL] Directionality wrong: {result2['directionality']}")
    
    if result2['offset_mm'] == 6.5:
        print("[PASS] Explicit offset preserved: 6.5 mm")
    else:
        print(f"[FAIL] Offset wrong: {result2['offset_mm']}")
        
    if result2['mounting_type'] == '2_piece_bolted':
        print("[PASS] Mounting type correct: 2_piece_bolted")
    else:
        print(f"[FAIL] Mounting type wrong: {result2['mounting_type']}")
else:
    print("[FAIL] Functional test 2 FAILED")

# ============================================================
# Test 3: Functional Test - Solid rotor with minimal data
# ============================================================
print("\n[TEST 3] Functional Test - Solid rotor with minimal data")
print("-" * 60)

sample3 = {
    "outer_diameter_mm": "280",
    "nominal_thickness_mm": "22",
    "hat_height_mm": "40",
    "overall_height_mm": "44",
    "center_bore_mm": "65.1",
    "bolt_circle_mm": "100",
    "bolt_hole_count": "4",
    "ventilation_type": "solid",
    "directionality": "non-directional",
    "catalog_ref": "BRM-280-S"
}

result3 = normalize_rotor(sample3, "brembo")
print(f"Input: {sample3}")
print(f"Output: {json.dumps(result3, indent=2)}")

if validate_against_schema(result3):
    print("[PASS] Functional test 3 PASSED - Schema validation successful")
    
    # Check offset calculation
    expected_offset = 44.0 - 40.0
    if result3['offset_mm'] == expected_offset:
        print(f"[PASS] Offset auto-calculated: {expected_offset} mm")
    else:
        print(f"❌ Offset calculation wrong: expected {expected_offset}, got {result3['offset_mm']}")
    
    if result3['brand'] == 'brembo':
        print("[PASS] Brand correctly set to source: brembo")
    else:
        print(f"[FAIL] Brand wrong: {result3['brand']}")
    
    if result3['catalog_ref'] == 'BRM-280-S':
        print("[PASS] Catalog ref from alternate field: BRM-280-S")
    else:
        print(f"[FAIL] Catalog ref wrong: {result3['catalog_ref']}")
    
    # Check optional fields are None when not provided
    if result3['rotor_weight_kg'] is None and result3['mounting_type'] is None:
        print("[PASS] Optional fields correctly set to None")
    else:
        print(f"[FAIL] Optional fields should be None")
else:
    print("[FAIL] Functional test 3 FAILED")

print("\n" + "="*60)
print("ALL TESTS COMPLETED")
print("="*60)
