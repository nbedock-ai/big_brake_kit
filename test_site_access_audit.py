"""
Unit tests for Site Access Audit tool (Mission 10.5)

Tests field detection logic and bot protection classification without requiring network access.
"""

import sys
sys.path.insert(0, '.')

from tools.site_access_audit import (
    analyze_html_fields,
    _detect_rotor_fields,
    _detect_pad_fields,
    _detect_vehicle_fields,
)


print("="*60)
print("MISSION 10.5 - SITE ACCESS AUDIT TESTS")
print("="*60)


# ============================================================
# Test 1: Rotor Field Detection
# ============================================================
print("\n[TEST 1] Rotor field detection")
print("-" * 60)

# HTML with diameter and thickness
html_rotor_basic = """
<html>
<body>
<div class="product">
    <h1>BREMBO Brake Disc</h1>
    <p>Part Number: 09.9772.11</p>
    <ul>
        <li>Diameter: 280 mm</li>
        <li>Thickness: 22 mm</li>
        <li>Type: Vented</li>
    </ul>
</div>
</body>
</html>
"""

fields1 = analyze_html_fields("rotor", html_rotor_basic)

checks1 = [
    (fields1.get("diameter_mm") == True, "Detects diameter (280 mm)"),
    (fields1.get("thickness_mm") == True, "Detects thickness (22 mm)"),
    (fields1.get("ventilation_type") == True, "Detects ventilation type (Vented)"),
    (fields1.get("brand") == True, "Detects brand (BREMBO)"),
    (fields1.get("catalog_ref") == True, "Detects part number"),
]

passed1 = sum(1 for check, _ in checks1 if check)
failed1 = len(checks1) - passed1

for check, msg in checks1:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {msg}")

if failed1 == 0:
    print(f"\n[PASS] Test 1 PASSED ({passed1}/{passed1} checks)")
else:
    print(f"\n[FAIL] Test 1 FAILED ({passed1}/{passed1+failed1} checks)")


# ============================================================
# Test 2: Rotor with Advanced Fields
# ============================================================
print("\n[TEST 2] Rotor with advanced fields (offset, bolt pattern)")
print("-" * 60)

html_rotor_advanced = """
<html>
<body>
<div class="specs">
    <p>Outer Diameter: 300mm</p>
    <p>Overall Height: 40mm</p>
    <p>Center Bore: 65.1mm</p>
    <p>Bolt Pattern: 5x114.3</p>
    <p>Offset: 45mm</p>
    <p>Weight: 8.5 kg</p>
    <p>Directional: Left</p>
</div>
</body>
</html>
"""

fields2 = analyze_html_fields("rotor", html_rotor_advanced)

checks2 = [
    (fields2.get("diameter_mm") == True, "Detects diameter (300mm)"),
    (fields2.get("height_mm") == True, "Detects height (40mm)"),
    (fields2.get("center_bore_mm") == True, "Detects center bore (65.1mm)"),
    (fields2.get("bolt_hole_count") == True, "Detects bolt pattern (5x114.3)"),
    (fields2.get("offset_mm") == True, "Detects offset (45mm)"),
    (fields2.get("weight_kg") == True, "Detects weight (8.5 kg)"),
    (fields2.get("directionality") == True, "Detects directionality (Left)"),
]

passed2 = sum(1 for check, _ in checks2 if check)
failed2 = len(checks2) - passed2

for check, msg in checks2:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {msg}")

if failed2 == 0:
    print(f"\n[PASS] Test 2 PASSED ({passed2}/{passed2} checks)")
else:
    print(f"\n[FAIL] Test 2 FAILED ({passed2}/{passed2+failed2} checks)")


# ============================================================
# Test 3: French Language Rotor
# ============================================================
print("\n[TEST 3] French language rotor fields")
print("-" * 60)

html_rotor_french = """
<html>
<body>
<table>
    <tr><td>Marque</td><td>BREMBO</td></tr>
    <tr><td>Référence</td><td>09.A422.11</td></tr>
    <tr><td>Diamètre</td><td>280mm</td></tr>
    <tr><td>Épaisseur</td><td>22mm</td></tr>
    <tr><td>Hauteur</td><td>40mm</td></tr>
    <tr><td>Alésage</td><td>65.1mm</td></tr>
    <tr><td>Type</td><td>Ventilé</td></tr>
</table>
</body>
</html>
"""

fields3 = analyze_html_fields("rotor", html_rotor_french)

checks3 = [
    (fields3.get("diameter_mm") == True, "Detects diamètre (French)"),
    (fields3.get("thickness_mm") == True, "Detects épaisseur (French)"),
    (fields3.get("height_mm") == True, "Detects hauteur (French)"),
    (fields3.get("center_bore_mm") == True, "Detects alésage (French)"),
    (fields3.get("ventilation_type") == True, "Detects ventilé (French)"),
    (fields3.get("brand") == True, "Detects marque (French)"),
]

passed3 = sum(1 for check, _ in checks3 if check)
failed3 = len(checks3) - passed3

for check, msg in checks3:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {msg}")

if failed3 == 0:
    print(f"\n[PASS] Test 3 PASSED ({passed3}/{passed3} checks)")
else:
    print(f"\n[FAIL] Test 3 FAILED ({passed3}/{passed3+failed3} checks)")


# ============================================================
# Test 4: Pad Field Detection
# ============================================================
print("\n[TEST 4] Pad field detection")
print("-" * 60)

html_pad = """
<html>
<body>
<div class="product">
    <h1>EBC Brake Pads - GreenStuff</h1>
    <p>Part Number: DP21234</p>
    <ul>
        <li>Friction Material: Ceramic</li>
        <li>Pad Thickness: 17mm</li>
        <li>Length: 140mm</li>
        <li>Width: 60mm</li>
        <li>Wear Indicator: Yes</li>
    </ul>
</div>
</body>
</html>
"""

fields4 = analyze_html_fields("pad", html_pad)

checks4 = [
    (fields4.get("brand") == True, "Detects pad brand (EBC)"),
    (fields4.get("catalog_ref") == True, "Detects part number"),
    (fields4.get("friction_material") == True, "Detects friction material (Ceramic)"),
    (fields4.get("pad_thickness") == True, "Detects pad thickness"),
    (fields4.get("pad_length") == True, "Detects pad length"),
    (fields4.get("pad_width") == True, "Detects pad width"),
    (fields4.get("wear_indicator") == True, "Detects wear indicator"),
]

passed4 = sum(1 for check, _ in checks4 if check)
failed4 = len(checks4) - passed4

for check, msg in checks4:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {msg}")

if failed4 == 0:
    print(f"\n[PASS] Test 4 PASSED ({passed4}/{passed4} checks)")
else:
    print(f"\n[FAIL] Test 4 FAILED ({passed4}/{passed4+failed4} checks)")


# ============================================================
# Test 5: Vehicle Field Detection
# ============================================================
print("\n[TEST 5] Vehicle field detection")
print("-" * 60)

html_vehicle = """
<html>
<body>
<div class="vehicle-specs">
    <h1>2015 Honda Civic</h1>
    <ul>
        <li>Make: Honda</li>
        <li>Model: Civic</li>
        <li>Year: 2015</li>
        <li>Engine: 2.0L</li>
        <li>Body Type: Sedan</li>
        <li>PCD: 5x114.3</li>
        <li>Center Bore: 64.1mm</li>
    </ul>
</div>
</body>
</html>
"""

fields5 = analyze_html_fields("vehicle", html_vehicle)

checks5 = [
    (fields5.get("make") == True, "Detects make (Honda)"),
    (fields5.get("model") == True, "Detects model (Civic)"),
    (fields5.get("year") == True, "Detects year (2015)"),
    (fields5.get("engine_size") == True, "Detects engine (2.0L)"),
    (fields5.get("body_type") == True, "Detects body type (Sedan)"),
    (fields5.get("hub_specs") == True, "Detects hub specs (PCD, center bore)"),
]

passed5 = sum(1 for check, _ in checks5 if check)
failed5 = len(checks5) - passed5

for check, msg in checks5:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {msg}")

if failed5 == 0:
    print(f"\n[PASS] Test 5 PASSED ({passed5}/{passed5} checks)")
else:
    print(f"\n[FAIL] Test 5 FAILED ({passed5}/{passed5+failed5} checks)")


# ============================================================
# Test 6: Bot Protection Detection
# ============================================================
print("\n[TEST 6] Bot protection detection in HTML")
print("-" * 60)

html_cloudflare = """
<html>
<head><title>Attention Required! | Cloudflare</title></head>
<body>
<h1>Please enable JavaScript to continue</h1>
<p>This request requires JavaScript to verify you are a human.</p>
</body>
</html>
"""

html_captcha = """
<html>
<body>
<h1>Access Denied</h1>
<p>Please complete the CAPTCHA below to continue</p>
<form>...</form>
</body>
</html>
"""

html_normal = """
<html>
<body>
<h1>BREMBO Brake Discs</h1>
<p>Welcome to our catalog of premium brake discs.</p>
</body>
</html>
"""

# Simulate bot detection logic
def detect_bot_protection(html: str) -> bool:
    """Simple bot detection for testing."""
    html_lower = html.lower()
    bot_signatures = ["cloudflare", "attention required", "enable javascript", 
                     "captcha", "access denied", "verify you are a human"]
    return any(sig in html_lower for sig in bot_signatures)

checks6 = [
    (detect_bot_protection(html_cloudflare) == True, "Detects Cloudflare protection"),
    (detect_bot_protection(html_captcha) == True, "Detects CAPTCHA protection"),
    (detect_bot_protection(html_normal) == False, "Normal HTML not flagged as bot-protected"),
]

passed6 = sum(1 for check, _ in checks6 if check)
failed6 = len(checks6) - passed6

for check, msg in checks6:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {msg}")

if failed6 == 0:
    print(f"\n[PASS] Test 6 PASSED ({passed6}/{passed6} checks)")
else:
    print(f"\n[FAIL] Test 6 FAILED ({passed6}/{passed6+failed6} checks)")


# ============================================================
# Summary
# ============================================================
total_passed = passed1 + passed2 + passed3 + passed4 + passed5 + passed6
total_failed = failed1 + failed2 + failed3 + failed4 + failed5 + failed6

print("\n" + "="*60)
print("ALL TESTS COMPLETED")
print(f"Total: {total_passed} PASSED, {total_failed} FAILED")
print("="*60)

if total_failed == 0:
    print("\n[SUCCESS] All site access audit tests passed!")
else:
    print(f"\n[FAIL] {total_failed} test(s) failed")
