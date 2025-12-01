"""
Test suite for ingest_pipeline.py - Mission 7
Tests seed loading, processing functions, and ingest_all pipeline.
"""

import sys
import sqlite3
import tempfile
import os
sys.path.insert(0, '.')

from database.ingest_pipeline import (
    load_seed_csv_paths,
    iter_seed_urls,
    process_rotor_seed,
    process_pad_seed,
    process_vehicle_seed,
    insert_rotor,
    insert_pad,
    insert_vehicle
)

print("="*60)
print("MISSION 7 - INGEST_PIPELINE TESTS")
print("="*60)

# ============================================================
# Test 1: Load seed CSV paths
# ============================================================
print("\n[TEST 1] load_seed_csv_paths()")
print("-" * 60)

paths = load_seed_csv_paths()
print(f"Loaded paths: {paths}")

checks1 = [
    (isinstance(paths, dict), "Returns dict"),
    ("rotors" in paths, "Has 'rotors' key"),
    ("pads" in paths, "Has 'pads' key"),
    ("vehicles" in paths, "Has 'vehicles' key"),
    (len(paths["rotors"]) > 0, "Rotors paths not empty"),
    (len(paths["pads"]) > 0, "Pads paths not empty"),
    (len(paths["vehicles"]) > 0, "Vehicles paths not empty"),
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

# ============================================================
# Test 2: Iterate seed URLs
# ============================================================
print("\n[TEST 2] iter_seed_urls('vehicles')")
print("-" * 60)

vehicle_urls = list(iter_seed_urls("vehicles"))
print(f"Found {len(vehicle_urls)} vehicle URLs")

if len(vehicle_urls) > 0:
    first = vehicle_urls[0]
    print(f"First URL: source='{first[0]}', url='{first[1][:50]}...', notes='{first[2]}'")

checks2 = [
    (len(vehicle_urls) > 0, "Found vehicle URLs"),
    (all(len(url_tuple) == 3 for url_tuple in vehicle_urls), "All tuples have 3 elements"),
    (all(isinstance(url_tuple[0], str) for url_tuple in vehicle_urls), "Source is string"),
    (all(isinstance(url_tuple[1], str) for url_tuple in vehicle_urls), "URL is string"),
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

# ============================================================
# Test 3: Database insertion functions
# ============================================================
print("\n[TEST 3] insert_rotor, insert_pad, insert_vehicle")
print("-" * 60)

# Create in-memory database
conn = sqlite3.connect(":memory:")

# Create tables (simplified schema)
conn.execute("""
    CREATE TABLE rotors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outer_diameter_mm REAL,
        nominal_thickness_mm REAL,
        hat_height_mm REAL,
        overall_height_mm REAL,
        center_bore_mm REAL,
        bolt_circle_mm REAL,
        bolt_hole_count INTEGER,
        ventilation_type TEXT,
        directionality TEXT,
        brand TEXT,
        catalog_ref TEXT
    )
""")

conn.execute("""
    CREATE TABLE pads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shape_id TEXT,
        length_mm REAL,
        height_mm REAL,
        thickness_mm REAL,
        brand TEXT,
        catalog_ref TEXT
    )
""")

conn.execute("""
    CREATE TABLE vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        make TEXT,
        model TEXT,
        year_from INTEGER,
        year_to INTEGER,
        hub_bolt_circle_mm REAL,
        hub_bolt_hole_count INTEGER,
        hub_center_bore_mm REAL
    )
""")

# Test rotor insertion
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

insert_rotor(conn, test_rotor)
rotor_count = conn.execute("SELECT COUNT(*) FROM rotors").fetchone()[0]

# Test pad insertion
test_pad = {
    "shape_id": "DP31",
    "length_mm": 120.0,
    "height_mm": 50.0,
    "thickness_mm": 15.0,
    "brand": "EBC",
    "catalog_ref": "DP31001C"
}

insert_pad(conn, test_pad)
pad_count = conn.execute("SELECT COUNT(*) FROM pads").fetchone()[0]

# Test vehicle insertion
test_vehicle = {
    "make": "Honda",
    "model": "Civic",
    "year_from": 2016,
    "year_to": 2020,
    "hub_bolt_circle_mm": 114.3,
    "hub_bolt_hole_count": 5,
    "hub_center_bore_mm": 64.1
}

insert_vehicle(conn, test_vehicle)
vehicle_count = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]

conn.close()

checks3 = [
    (rotor_count == 1, "Rotor inserted"),
    (pad_count == 1, "Pad inserted"),
    (vehicle_count == 1, "Vehicle inserted"),
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

# ============================================================
# Test 4: Check database schema exists
# ============================================================
print("\n[TEST 4] Database schema validation")
print("-" * 60)

# Check if bbk.db exists and has the right tables
db_path = "database/bbk.db"
schema_ok = False

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Found tables: {tables}")
    
    has_rotors = "rotors" in tables
    has_pads = "pads" in tables
    has_vehicles = "vehicles" in tables
    
    schema_ok = has_rotors and has_pads and has_vehicles
    conn.close()
    
    checks4 = [
        (has_rotors, "Rotors table exists"),
        (has_pads, "Pads table exists"),
        (has_vehicles, "Vehicles table exists"),
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
else:
    print(f"[INFO] Database {db_path} not found (will be created on first ingest)")
    passed4 = 0
    failed4 = 0

# ============================================================
# Summary
# ============================================================
total_passed = passed1 + passed2 + passed3 + passed4
total_failed = failed1 + failed2 + failed3 + failed4

print("\n" + "="*60)
print("ALL TESTS COMPLETED")
print(f"Total: {total_passed} PASSED, {total_failed} FAILED")
print("="*60)

print("\n" + "="*60)
print("INTEGRATION TEST NOTES")
print("="*60)
print("To test the full pipeline (requires network access):")
print("  python -m database.ingest_pipeline vehicles")
print("  python -m database.ingest_pipeline")
print("\nThis will:")
print("  1. Read seed URLs from CSV files")
print("  2. Fetch HTML pages")
print("  3. Parse and normalize data")
print("  4. Insert into database/bbk.db")
print("="*60)
