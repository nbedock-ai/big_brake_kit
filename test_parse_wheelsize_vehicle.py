"""
Test suite for parse_wheelsize_vehicle_page function.
Mission 5 - Smoke and functional tests for raw vehicle data extraction.
"""

import sys
sys.path.insert(0, '.')

from data_scraper.html_scraper import parse_wheelsize_vehicle_page

print("="*60)
print("MISSION 5 - PARSE_WHEELSIZE_VEHICLE_PAGE TESTS")
print("="*60)

# ============================================================
# Test 1: Smoke Test - Minimal HTML
# ============================================================
print("\n[TEST 1] Smoke Test - Minimal vehicle table")
print("-" * 60)

html_smoke = """
<html>
<head><title>Honda Civic Specs</title></head>
<body>
    <h1>Honda Civic 2016-2020</h1>
    <table class="specifications">
        <tr><th>Make</th><td>Honda</td></tr>
        <tr><th>Model</th><td>Civic</td></tr>
        <tr><th>Generation</th><td>10th Gen</td></tr>
        <tr><th>Year From</th><td>2016</td></tr>
        <tr><th>Year To</th><td>2020</td></tr>
        <tr><th>PCD</th><td>5x114.3</td></tr>
        <tr><th>Center Bore</th><td>64.1mm</td></tr>
    </table>
</body>
</html>
"""

result1 = parse_wheelsize_vehicle_page(html_smoke)
print(f"Extracted fields: {list(result1.keys())}")
print(f"Output: {result1}")

# Validate smoke test
checks = [
    (result1.get('make') == 'Honda', "Make: Honda"),
    (result1.get('model') == 'Civic', "Model: Civic"),
    (result1.get('generation') == '10th Gen', "Generation: 10th Gen"),
    (result1.get('year_from_raw') == '2016', "Year from raw: 2016"),
    (result1.get('year_to_raw') == '2020', "Year to raw: 2020"),
    (result1.get('hub_bolt_pattern_raw') == '5x114.3', "Bolt pattern raw: 5x114.3"),
    (result1.get('hub_bolt_hole_count_raw') == '5', "Bolt holes parsed: 5"),
    (result1.get('hub_bolt_circle_mm_raw') == '114.3', "Bolt circle parsed: 114.3"),
    (result1.get('hub_center_bore_mm_raw') == '64.1mm', "Center bore raw: 64.1mm"),
]

passed = 0
failed = 0
for check, message in checks:
    if check:
        print(f"[PASS] {message}")
        passed += 1
    else:
        print(f"[FAIL] {message}")
        failed += 1

if failed == 0:
    print(f"\n[PASS] Smoke test PASSED ({passed}/{passed} checks)")
else:
    print(f"\n[FAIL] Smoke test FAILED ({passed}/{passed+failed} checks)")

# ============================================================
# Test 2: Functional Test - Complete specifications
# ============================================================
print("\n[TEST 2] Functional Test - Complete vehicle/wheel/rotor specs")
print("-" * 60)

html_functional = """
<html>
<body>
    <h1>BMW 3 Series Vehicle Specifications</h1>
    <table class="vehicle-specs">
        <tr><th>Make</th><td>BMW</td></tr>
        <tr><th>Model</th><td>3 Series</td></tr>
        <tr><th>Generation</th><td>E90</td></tr>
        <tr><th>Year From</th><td>2005</td></tr>
        <tr><th>Year To</th><td>2012</td></tr>
        <tr><th>Bolt Pattern</th><td>5x120</td></tr>
        <tr><th>Center Bore</th><td>72.6</td></tr>
        <tr><th>Front Wheel Width</th><td>7.5 inches</td></tr>
        <tr><th>Front Wheel Diameter</th><td>17 inches</td></tr>
        <tr><th>Rear Wheel Width</th><td>8.0 inches</td></tr>
        <tr><th>Rear Wheel Diameter</th><td>17 inches</td></tr>
        <tr><th>Front Tire</th><td>225/45R17</td></tr>
        <tr><th>Rear Tire</th><td>245/40R17</td></tr>
        <tr><th>Front Rotor Diameter</th><td>300mm</td></tr>
        <tr><th>Front Rotor Thickness</th><td>22mm</td></tr>
        <tr><th>Rear Rotor Diameter</th><td>294mm</td></tr>
        <tr><th>Rear Rotor Thickness</th><td>20mm</td></tr>
    </table>
</body>
</html>
"""

result2 = parse_wheelsize_vehicle_page(html_functional)
print(f"Extracted fields: {list(result2.keys())}")
print(f"Output: {result2}")

# Validate functional test
checks2 = [
    (result2.get('make') == 'BMW', "Make: BMW"),
    (result2.get('model') == '3 Series', "Model: 3 Series"),
    (result2.get('generation') == 'E90', "Generation: E90"),
    (result2.get('year_from_raw') == '2005', "Year from: 2005"),
    (result2.get('year_to_raw') == '2012', "Year to: 2012"),
    (result2.get('hub_bolt_pattern_raw') == '5x120', "Bolt pattern: 5x120"),
    (result2.get('hub_bolt_hole_count_raw') == '5', "Bolt holes: 5"),
    (result2.get('hub_bolt_circle_mm_raw') == '120', "Bolt circle: 120"),
    (result2.get('hub_center_bore_mm_raw') == '72.6', "Center bore: 72.6"),
    (result2.get('front_wheel_width_in_raw') == '7.5 inches', "Front wheel width: 7.5 inches"),
    (result2.get('front_wheel_diameter_in_raw') == '17 inches', "Front wheel diameter: 17 inches"),
    (result2.get('rear_wheel_width_in_raw') == '8.0 inches', "Rear wheel width: 8.0 inches"),
    (result2.get('rear_wheel_diameter_in_raw') == '17 inches', "Rear wheel diameter: 17 inches"),
    (result2.get('front_tire_dimensions_raw') == '225/45R17', "Front tire: 225/45R17"),
    (result2.get('rear_tire_dimensions_raw') == '245/40R17', "Rear tire: 245/40R17"),
    (result2.get('front_rotor_outer_diameter_mm_raw') == '300mm', "Front rotor diameter: 300mm"),
    (result2.get('front_rotor_thickness_mm_raw') == '22mm', "Front rotor thickness: 22mm"),
    (result2.get('rear_rotor_outer_diameter_mm_raw') == '294mm', "Rear rotor diameter: 294mm"),
    (result2.get('rear_rotor_thickness_mm_raw') == '20mm', "Rear rotor thickness: 20mm"),
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
    print(f"\n[PASS] Functional test PASSED ({passed2}/{passed2} checks)")
else:
    print(f"\n[FAIL] Functional test FAILED ({passed2}/{passed2+failed2} checks)")

# ============================================================
# Test 3: Definition List Format
# ============================================================
print("\n[TEST 3] Alternative HTML Format - Definition List")
print("-" * 60)

html_dl = """
<html>
<body>
    <h1>Volkswagen Golf</h1>
    <dl class="specifications">
        <dt>Make</dt><dd>Volkswagen</dd>
        <dt>Model</dt><dd>Golf</dd>
        <dt>Generation</dt><dd>Mk7</dd>
        <dt>PCD</dt><dd>5x112</dd>
        <dt>Center Bore</dt><dd>57.1mm</dd>
    </dl>
</body>
</html>
"""

result3 = parse_wheelsize_vehicle_page(html_dl)
print(f"Extracted fields: {list(result3.keys())}")
print(f"Output: {result3}")

# Validate DL test
checks3 = [
    (result3.get('make') == 'Volkswagen', "Make from DL: Volkswagen"),
    (result3.get('model') == 'Golf', "Model from DL: Golf"),
    (result3.get('generation') == 'Mk7', "Generation from DL: Mk7"),
    (result3.get('hub_bolt_pattern_raw') == '5x112', "Bolt pattern: 5x112"),
    (result3.get('hub_bolt_hole_count_raw') == '5', "Bolt holes parsed: 5"),
    (result3.get('hub_bolt_circle_mm_raw') == '112', "Bolt circle parsed: 112"),
    (result3.get('hub_center_bore_mm_raw') == '57.1mm', "Center bore: 57.1mm"),
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
    print(f"\n[PASS] Definition list test PASSED ({passed3}/{passed3} checks)")
else:
    print(f"\n[FAIL] Definition list test FAILED ({passed3}/{passed3+failed3} checks)")

# ============================================================
# Test 4: Title extraction fallback
# ============================================================
print("\n[TEST 4] Title/H1 Extraction Fallback")
print("-" * 60)

html_title = """
<html>
<body>
    <h1>Toyota Camry 2018-2022</h1>
    <table>
        <tr><th>PCD</th><td>5x114.3</td></tr>
        <tr><th>Center Bore</th><td>60.1</td></tr>
    </table>
</body>
</html>
"""

result4 = parse_wheelsize_vehicle_page(html_title)
print(f"Extracted fields: {list(result4.keys())}")
print(f"Output: {result4}")

# Validate title extraction
checks4 = [
    (result4.get('make') == 'Toyota', "Make from title: Toyota"),
    (result4.get('model') == 'Camry', "Model from title: Camry"),
    (result4.get('hub_bolt_pattern_raw') == '5x114.3', "Bolt pattern: 5x114.3"),
    (result4.get('hub_center_bore_mm_raw') == '60.1', "Center bore: 60.1"),
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
    print(f"\n[PASS] Title extraction test PASSED ({passed4}/{passed4} checks)")
else:
    print(f"\n[FAIL] Title extraction test FAILED ({passed4}/{passed4+failed4} checks)")

print("\n" + "="*60)
print("ALL TESTS COMPLETED")
print(f"Total: {passed+passed2+passed3+passed4} PASSED, {failed+failed2+failed3+failed4} FAILED")
print("="*60)
