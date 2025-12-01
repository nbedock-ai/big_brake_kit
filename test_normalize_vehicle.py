"""
Test suite for normalize_vehicle function.
Mission 6 - Vehicle data normalization from Wheel-Size raw format.
"""

import sys
sys.path.insert(0, '.')

from data_scraper.html_scraper import normalize_vehicle

print("="*60)
print("MISSION 6 - NORMALIZE_VEHICLE TESTS")
print("="*60)

# ============================================================
# Test 1: Complete Wheel-Size data with all fields
# ============================================================
print("\n[TEST 1] Complete Wheel-Size data normalization")
print("-" * 60)

raw1 = {
    "make": "Honda",
    "model": "Civic",
    "generation": "10th Gen",
    "year_from_raw": "2016",
    "year_to_raw": "2020",
    "hub_bolt_pattern_raw": "5x114.3",
    "hub_center_bore_mm_raw": "64.1mm",
    "front_rotor_outer_diameter_mm_raw": "300mm",
    "front_rotor_thickness_mm_raw": "24mm",
    "rear_rotor_outer_diameter_mm_raw": "282mm",
    "rear_rotor_thickness_mm_raw": "10mm"
}

result1 = normalize_vehicle(raw1, "wheelsize")
print(f"Input: {raw1}")
print(f"\nOutput: {result1}")

checks1 = [
    (result1["make"] == "Honda", "Make: Honda"),
    (result1["model"] == "Civic", "Model: Civic"),
    (result1["generation"] == "10th Gen", "Generation: 10th Gen"),
    (result1["year_from"] == 2016, "year_from: 2016 (int)"),
    (result1["year_to"] == 2020, "year_to: 2020 (int)"),
    (result1["hub_bolt_hole_count"] == 5, "hub_bolt_hole_count: 5 (from pattern)"),
    (result1["hub_bolt_circle_mm"] == 114.3, "hub_bolt_circle_mm: 114.3 (from pattern)"),
    (result1["hub_center_bore_mm"] == 64.1, "hub_center_bore_mm: 64.1 (mm stripped)"),
    (result1["max_rotor_diameter_mm"] == 300.0, "max_rotor_diameter_mm: 300.0 (max of front/rear)"),
    (result1["rotor_thickness_min_mm"] == 10.0, "rotor_thickness_min_mm: 10.0 (min of front/rear)"),
    (result1["rotor_thickness_max_mm"] == 24.0, "rotor_thickness_max_mm: 24.0 (max of front/rear)"),
    (result1["knuckle_bolt_spacing_mm"] is None, "knuckle_bolt_spacing_mm: None (Wheel-Size)"),
    (result1["knuckle_bolt_orientation_deg"] is None, "knuckle_bolt_orientation_deg: None"),
    (result1["wheel_inner_barrel_clearance_mm"] is None, "wheel_inner_barrel_clearance_mm: None"),
]

passed1 = 0
failed1 = 0
for check, message in checks1:
    if check:
        print(f"[PASS] {message}")
        passed1 += 1
    else:
        print(f"[FAIL] {message}")
        failed1 += 1

if failed1 == 0:
    print(f"\n[PASS] Test 1 PASSED ({passed1}/{passed1} checks)")
else:
    print(f"\n[FAIL] Test 1 FAILED ({passed1}/{passed1+failed1} checks)")

# ============================================================
# Test 2: Open-ended year range (2016-)
# ============================================================
print("\n[TEST 2] Open-ended year range (year_to = None)")
print("-" * 60)

raw2 = {
    "make": "Tesla",
    "model": "Model 3",
    "years_raw": "2017-",
    "hub_bolt_pattern_raw": "5x114.3",
    "hub_center_bore_mm_raw": "64.1"
}

result2 = normalize_vehicle(raw2, "wheelsize")
print(f"Input: {raw2}")
print(f"\nOutput: {result2}")

checks2 = [
    (result2["make"] == "Tesla", "Make: Tesla"),
    (result2["model"] == "Model 3", "Model: Model 3"),
    (result2["year_from"] == 2017, "year_from: 2017 (from years_raw)"),
    (result2["year_to"] is None, "year_to: None (open-ended)"),
    (result2["generation"] is None, "generation: None (optional)"),
]

passed2 = 0
failed2 = 0
for check, message in checks2:
    if check:
        print(f"[PASS] {message}")
        passed2 += 1
    else:
        print(f"[FAIL] {message}")
        failed2 += 1

if failed2 == 0:
    print(f"\n[PASS] Test 2 PASSED ({passed2}/{passed2} checks)")
else:
    print(f"\n[FAIL] Test 2 FAILED ({passed2}/{passed2+failed2} checks)")

# ============================================================
# Test 3: No OEM rotor data (optional fields)
# ============================================================
print("\n[TEST 3] No OEM rotor data")
print("-" * 60)

raw3 = {
    "make": "Volkswagen",
    "model": "Golf",
    "generation": "Mk7",
    "year_from_raw": "2013",
    "year_to_raw": "2020",
    "hub_bolt_pattern_raw": "5x112",
    "hub_center_bore_mm_raw": "57.1"
}

result3 = normalize_vehicle(raw3, "wheelsize")
print(f"Input: {raw3}")
print(f"\nOutput: {result3}")

checks3 = [
    (result3["make"] == "Volkswagen", "Make: Volkswagen"),
    (result3["model"] == "Golf", "Model: Golf"),
    (result3["max_rotor_diameter_mm"] is None, "max_rotor_diameter_mm: None (no data)"),
    (result3["rotor_thickness_min_mm"] is None, "rotor_thickness_min_mm: None"),
    (result3["rotor_thickness_max_mm"] is None, "rotor_thickness_max_mm: None"),
]

passed3 = 0
failed3 = 0
for check, message in checks3:
    if check:
        print(f"[PASS] {message}")
        passed3 += 1
    else:
        print(f"[FAIL] {message}")
        failed3 += 1

if failed3 == 0:
    print(f"\n[PASS] Test 3 PASSED ({passed3}/{passed3} checks)")
else:
    print(f"\n[FAIL] Test 3 FAILED ({passed3}/{passed3+failed3} checks)")

# ============================================================
# Test 4: PCD from explicit fields (not pattern)
# ============================================================
print("\n[TEST 4] PCD from explicit hub_bolt_hole_count_raw and hub_bolt_circle_mm_raw")
print("-" * 60)

raw4 = {
    "make": "BMW",
    "model": "3 Series",
    "year_from_raw": "2005",
    "year_to_raw": "2012",
    "hub_bolt_hole_count_raw": "5",
    "hub_bolt_circle_mm_raw": "120",
    "hub_center_bore_mm_raw": "72.6mm"
}

result4 = normalize_vehicle(raw4, "wheelsize")
print(f"Input: {raw4}")
print(f"\nOutput: {result4}")

checks4 = [
    (result4["hub_bolt_hole_count"] == 5, "hub_bolt_hole_count: 5 (explicit)"),
    (result4["hub_bolt_circle_mm"] == 120.0, "hub_bolt_circle_mm: 120.0 (explicit)"),
    (result4["hub_center_bore_mm"] == 72.6, "hub_center_bore_mm: 72.6"),
]

passed4 = 0
failed4 = 0
for check, message in checks4:
    if check:
        print(f"[PASS] {message}")
        passed4 += 1
    else:
        print(f"[FAIL] {message}")
        failed4 += 1

if failed4 == 0:
    print(f"\n[PASS] Test 4 PASSED ({passed4}/{passed4} checks)")
else:
    print(f"\n[FAIL] Test 4 FAILED ({passed4}/{passed4+failed4} checks)")

# ============================================================
# Test 5: Invalid data - missing make/model
# ============================================================
print("\n[TEST 5] Invalid data - missing required fields")
print("-" * 60)

raw5_missing_make = {
    "model": "Civic",
    "hub_bolt_pattern_raw": "5x114.3",
    "hub_center_bore_mm_raw": "64.1"
}

try:
    result5 = normalize_vehicle(raw5_missing_make, "wheelsize")
    print(f"[FAIL] Should have raised ValueError for missing 'make'")
    passed5 = 0
    failed5 = 1
except ValueError as e:
    print(f"[PASS] Correctly raised ValueError: {e}")
    passed5 = 1
    failed5 = 0

# ============================================================
# Test 6: Invalid data - missing PCD
# ============================================================
print("\n[TEST 6] Invalid data - missing PCD")
print("-" * 60)

raw6_missing_pcd = {
    "make": "Honda",
    "model": "Civic",
    "year_from_raw": "2016",
    "hub_center_bore_mm_raw": "64.1"
}

try:
    result6 = normalize_vehicle(raw6_missing_pcd, "wheelsize")
    print(f"[FAIL] Should have raised ValueError for missing PCD")
    passed6 = 0
    failed6 = 1
except ValueError as e:
    print(f"[PASS] Correctly raised ValueError: {e}")
    passed6 = 1
    failed6 = 0

# ============================================================
# Test 7: Unsupported source
# ============================================================
print("\n[TEST 7] Unsupported source")
print("-" * 60)

raw7 = {
    "make": "Honda",
    "model": "Civic",
    "year_from_raw": "2016",
    "hub_bolt_pattern_raw": "5x114.3",
    "hub_center_bore_mm_raw": "64.1"
}

try:
    result7 = normalize_vehicle(raw7, "autodata")
    print(f"[FAIL] Should have raised NotImplementedError for unsupported source")
    passed7 = 0
    failed7 = 1
except NotImplementedError as e:
    print(f"[PASS] Correctly raised NotImplementedError: {e}")
    passed7 = 1
    failed7 = 0

# ============================================================
# Test 8: Years from years_raw format "2016-2020"
# ============================================================
print("\n[TEST 8] Years parsed from years_raw 'YYYY-YYYY' format")
print("-" * 60)

raw8 = {
    "make": "Toyota",
    "model": "Camry",
    "years_raw": "2018-2022",
    "hub_bolt_pattern_raw": "5x114.3",
    "hub_center_bore_mm_raw": "60.1"
}

result8 = normalize_vehicle(raw8, "wheelsize")
print(f"Input: {raw8}")
print(f"\nOutput: {result8}")

checks8 = [
    (result8["year_from"] == 2018, "year_from: 2018 (from years_raw)"),
    (result8["year_to"] == 2022, "year_to: 2022 (from years_raw)"),
]

passed8 = 0
failed8 = 0
for check, message in checks8:
    if check:
        print(f"[PASS] {message}")
        passed8 += 1
    else:
        print(f"[FAIL] {message}")
        failed8 += 1

if failed8 == 0:
    print(f"\n[PASS] Test 8 PASSED ({passed8}/{passed8} checks)")
else:
    print(f"\n[FAIL] Test 8 FAILED ({passed8}/{passed8+failed8} checks)")

# ============================================================
# Summary
# ============================================================
total_passed = passed1 + passed2 + passed3 + passed4 + passed5 + passed6 + passed7 + passed8
total_failed = failed1 + failed2 + failed3 + failed4 + failed5 + failed6 + failed7 + failed8

print("\n" + "="*60)
print("ALL TESTS COMPLETED")
print(f"Total: {total_passed} PASSED, {total_failed} FAILED")
print("="*60)
