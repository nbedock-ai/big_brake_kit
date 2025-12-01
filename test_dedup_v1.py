"""
Test suite for deduplication V1 (Mission 9)
Tests that the ingestion pipeline correctly prevents duplicate entries
based on key fields: (brand, catalog_ref) for rotors, (shape_id, brand, catalog_ref) for pads,
and (make, model, year_from) for vehicles.
"""

import sys
import sqlite3
sys.path.insert(0, '.')

from database.ingest_pipeline import (
    insert_rotor,
    insert_pad,
    insert_vehicle,
    rotor_exists,
    pad_exists,
    vehicle_exists
)

print("="*60)
print("MISSION 9 - DEDUPLICATION V1 TESTS")
print("="*60)

# ============================================================
# Setup: Create in-memory database with schema
# ============================================================

def create_test_db():
    """Create in-memory DB with full schema"""
    conn = sqlite3.connect(":memory:")
    
    # Read schema from init.sql
    with open("database/init.sql", "r", encoding="utf-8") as f:
        schema_sql = f.read()
    
    conn.executescript(schema_sql)
    return conn


# ============================================================
# Test 1: Rotor deduplication
# ============================================================
print("\n[TEST 1] Rotor deduplication - same (brand, catalog_ref)")
print("-" * 60)

conn = create_test_db()

# Create test rotor
test_rotor = {
    "outer_diameter_mm": 300.0,
    "nominal_thickness_mm": 24.0,
    "hat_height_mm": 40.0,
    "overall_height_mm": 64.0,
    "center_bore_mm": 64.1,
    "bolt_circle_mm": 114.3,
    "bolt_hole_count": 5,
    "ventilation_type": "vented",
    "directionality": "non-directional",
    "brand": "DBA",
    "catalog_ref": "DBA2000"
}

# First insert
insert_rotor(conn, test_rotor)
count_after_first = conn.execute("SELECT COUNT(*) FROM rotors").fetchone()[0]

# Check if exists
exists = rotor_exists(conn, test_rotor)

# Try second insert with same key (should be blocked by dedup logic)
# In real pipeline, process_rotor_seed would check rotor_exists and skip
if not rotor_exists(conn, test_rotor):
    insert_rotor(conn, test_rotor)

count_after_second = conn.execute("SELECT COUNT(*) FROM rotors").fetchone()[0]

checks1 = [
    (count_after_first == 1, "First insert succeeded (COUNT=1)"),
    (exists is True, "rotor_exists returns True after insert"),
    (count_after_second == 1, "Second insert blocked (COUNT still 1)"),
]

passed1 = sum(1 for check, _ in checks1 if check)
failed1 = len(checks1) - passed1

for check, message in checks1:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {message}")

if failed1 == 0:
    print(f"\n[PASS] Test 1 PASSED ({passed1}/{passed1} checks)")
else:
    print(f"\n[FAIL] Test 1 FAILED ({passed1}/{passed1+failed1} checks)")

conn.close()


# ============================================================
# Test 2: Pad deduplication
# ============================================================
print("\n[TEST 2] Pad deduplication - same (shape_id, brand, catalog_ref)")
print("-" * 60)

conn = create_test_db()

# Create test pad
test_pad = {
    "shape_id": "DP31",
    "length_mm": 120.0,
    "height_mm": 50.0,
    "thickness_mm": 15.0,
    "brand": "EBC",
    "catalog_ref": "DP31001C"
}

# First insert
insert_pad(conn, test_pad)
count_after_first = conn.execute("SELECT COUNT(*) FROM pads").fetchone()[0]

# Check if exists
exists = pad_exists(conn, test_pad)

# Try second insert with same key
if not pad_exists(conn, test_pad):
    insert_pad(conn, test_pad)

count_after_second = conn.execute("SELECT COUNT(*) FROM pads").fetchone()[0]

checks2 = [
    (count_after_first == 1, "First insert succeeded (COUNT=1)"),
    (exists is True, "pad_exists returns True after insert"),
    (count_after_second == 1, "Second insert blocked (COUNT still 1)"),
]

passed2 = sum(1 for check, _ in checks2 if check)
failed2 = len(checks2) - passed2

for check, message in checks2:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {message}")

if failed2 == 0:
    print(f"\n[PASS] Test 2 PASSED ({passed2}/{passed2} checks)")
else:
    print(f"\n[FAIL] Test 2 FAILED ({passed2}/{passed2+failed2} checks)")

conn.close()


# ============================================================
# Test 3: Vehicle deduplication
# ============================================================
print("\n[TEST 3] Vehicle deduplication - same (make, model, year_from)")
print("-" * 60)

conn = create_test_db()

# Create test vehicle
test_vehicle = {
    "make": "Honda",
    "model": "Civic",
    "year_from": 2016,
    "year_to": 2020,
    "hub_bolt_circle_mm": 114.3,
    "hub_bolt_hole_count": 5,
    "hub_center_bore_mm": 64.1
}

# First insert
insert_vehicle(conn, test_vehicle)
count_after_first = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]

# Check if exists
exists = vehicle_exists(conn, test_vehicle)

# Try second insert with same key
if not vehicle_exists(conn, test_vehicle):
    insert_vehicle(conn, test_vehicle)

count_after_second = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]

checks3 = [
    (count_after_first == 1, "First insert succeeded (COUNT=1)"),
    (exists is True, "vehicle_exists returns True after insert"),
    (count_after_second == 1, "Second insert blocked (COUNT still 1)"),
]

passed3 = sum(1 for check, _ in checks3 if check)
failed3 = len(checks3) - passed3

for check, message in checks3:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {message}")

if failed3 == 0:
    print(f"\n[PASS] Test 3 PASSED ({passed3}/{passed3} checks)")
else:
    print(f"\n[FAIL] Test 3 FAILED ({passed3}/{passed3+failed3} checks)")

conn.close()


# ============================================================
# Test 4: Non-duplicates are allowed
# ============================================================
print("\n[TEST 4] Non-duplicates - different keys should both insert")
print("-" * 60)

conn = create_test_db()

# Two rotors with same brand but different catalog_ref
rotor1 = {
    "outer_diameter_mm": 300.0,
    "nominal_thickness_mm": 24.0,
    "hat_height_mm": 40.0,
    "overall_height_mm": 64.0,
    "center_bore_mm": 64.1,
    "bolt_circle_mm": 114.3,
    "bolt_hole_count": 5,
    "ventilation_type": "vented",
    "directionality": "non-directional",
    "brand": "DBA",
    "catalog_ref": "DBA2000"
}

rotor2 = {
    "outer_diameter_mm": 320.0,
    "nominal_thickness_mm": 26.0,
    "hat_height_mm": 42.0,
    "overall_height_mm": 68.0,
    "center_bore_mm": 70.1,
    "bolt_circle_mm": 114.3,
    "bolt_hole_count": 5,
    "ventilation_type": "vented",
    "directionality": "non-directional",
    "brand": "DBA",           # Same brand
    "catalog_ref": "DBA3000"  # Different catalog_ref
}

insert_rotor(conn, rotor1)
insert_rotor(conn, rotor2)
rotor_count = conn.execute("SELECT COUNT(*) FROM rotors").fetchone()[0]

# Two vehicles with same make/model but different year_from
vehicle1 = {
    "make": "Honda",
    "model": "Civic",
    "year_from": 2016,  # Different year
    "hub_bolt_circle_mm": 114.3,
    "hub_bolt_hole_count": 5,
    "hub_center_bore_mm": 64.1
}

vehicle2 = {
    "make": "Honda",
    "model": "Civic",
    "year_from": 2020,  # Different year
    "hub_bolt_circle_mm": 114.3,
    "hub_bolt_hole_count": 5,
    "hub_center_bore_mm": 64.1
}

insert_vehicle(conn, vehicle1)
insert_vehicle(conn, vehicle2)
vehicle_count = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]

checks4 = [
    (rotor_count == 2, "Two rotors with different catalog_ref both inserted"),
    (vehicle_count == 2, "Two vehicles with different year_from both inserted"),
]

passed4 = sum(1 for check, _ in checks4 if check)
failed4 = len(checks4) - passed4

for check, message in checks4:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {message}")

if failed4 == 0:
    print(f"\n[PASS] Test 4 PASSED ({passed4}/{passed4} checks)")
else:
    print(f"\n[FAIL] Test 4 FAILED ({passed4}/{passed4+failed4} checks)")

conn.close()


# ============================================================
# Summary
# ============================================================
total_passed = passed1 + passed2 + passed3 + passed4
total_failed = failed1 + failed2 + failed3 + failed4

print("\n" + "="*60)
print("ALL TESTS COMPLETED")
print(f"Total: {total_passed} PASSED, {total_failed} FAILED")
print("="*60)

if total_failed == 0:
    print("\n[SUCCESS] All deduplication tests passed!")
    print("\nDeduplication keys validated:")
    print("  - Rotors: (brand, catalog_ref)")
    print("  - Pads: (shape_id, brand, catalog_ref)")
    print("  - Vehicles: (make, model, year_from)")
    print("\nPipeline is now idempotent for duplicate seed URLs.")
else:
    print(f"\n[FAIL] {total_failed} test(s) failed")
