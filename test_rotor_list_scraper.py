"""
Test suite for multi-list rotor scraping (Mission 10.2).

Tests the html_rotor_list_scraper module and integration with ingest_pipeline.
"""

import sys
import sqlite3
sys.path.insert(0, '.')

from data_scraper.html_rotor_list_scraper import (
    parse_rotor_list_page,
    SimpleTableParser,
    extract_dimension,
    clean_text
)

print("="*60)
print("MISSION 10.2 - MULTI-LIST ROTOR SCRAPING TESTS")
print("="*60)


# ============================================================
# Test 1: Helper Functions
# ============================================================
print("\n[TEST 1] Helper functions - extract_dimension(), clean_text()")
print("-" * 60)

checks1 = [
    (extract_dimension("280mm diameter", "diameter") == 280.0, "Extract diameter from text"),
    (extract_dimension("Thickness: 22.5mm", "thickness") == 22.5, "Extract thickness from text"),
    (extract_dimension("offset 45mm", "offset") == 45.0, "Extract offset from text"),
    (extract_dimension("no dimension here", "diameter") is None, "Return None when not found"),
    (clean_text("  extra   spaces  ") == "extra spaces", "Clean whitespace"),
    (clean_text("text&nbsp;with&nbsp;nbsp") == "text with nbsp", "Clean HTML entities"),
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
# Test 2: SimpleTableParser
# ============================================================
print("\n[TEST 2] SimpleTableParser - HTML table extraction")
print("-" * 60)

sample_table_html = """
<html>
<body>
<table>
    <tr>
        <th>Brand</th>
        <th>Part Number</th>
        <th>Diameter</th>
    </tr>
    <tr>
        <td>Bosch</td>
        <td>0986479XXX</td>
        <td>280mm</td>
    </tr>
    <tr>
        <td>TRW</td>
        <td>DF4567</td>
        <td>300mm</td>
    </tr>
</table>
</body>
</html>
"""

parser = SimpleTableParser()
parser.feed(sample_table_html)
rows = parser.get_rows()

checks2 = [
    (len(rows) == 3, f"Extracted 3 rows (got {len(rows)})"),
    (len(rows) > 0 and rows[0][0] == "Brand", "Header row correct"),
    (len(rows) > 1 and rows[1][0] == "Bosch", "First data row correct"),
    (len(rows) > 2 and rows[2][0] == "TRW", "Second data row correct"),
    (len(rows) > 1 and rows[1][2] == "280mm", "Diameter column correct"),
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
# Test 3: parse_rotor_list_page - NotImplementedError
# ============================================================
print("\n[TEST 3] parse_rotor_list_page - unimplemented sources")
print("-" * 60)

try:
    result = parse_rotor_list_page("<html></html>", "unknown_source")
    checks3 = [(False, "Should raise NotImplementedError for unknown source")]
except NotImplementedError as e:
    checks3 = [
        (True, "Raises NotImplementedError for unknown source"),
        ("not implemented" in str(e).lower(), "Error message mentions 'not implemented'"),
    ]
except Exception as e:
    checks3 = [(False, f"Wrong exception type: {type(e).__name__}")]

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
# Test 4: AutoDoc list parser with fixture
# ============================================================
print("\n[TEST 4] AutoDoc list parser - fixture extraction")
print("-" * 60)

from pathlib import Path

def load_fixture(name: str) -> str:
    """Load HTML fixture from tests/fixtures/rotor_lists/"""
    base = Path(__file__).parent / "tests" / "fixtures" / "rotor_lists"
    return (base / name).read_text(encoding="utf-8")

try:
    autodoc_html = load_fixture("autodoc_list_01.html")
    autodoc_rotors = parse_rotor_list_page(autodoc_html, "autodoc")
    
    checks4 = [
        (isinstance(autodoc_rotors, list), "Returns list"),
        (len(autodoc_rotors) >= 5, f"Extracts at least 5 rotors (got {len(autodoc_rotors)})"),
    ]
    
    # Check first rotor has required fields
    if len(autodoc_rotors) > 0:
        first = autodoc_rotors[0]
        checks4.extend([
            (first.get("brand") is not None and first.get("brand") != "", "First rotor has brand"),
            (first.get("catalog_ref") is not None and first.get("catalog_ref") != "", "First rotor has catalog_ref"),
            (first.get("outer_diameter_mm") is not None, "First rotor has diameter"),
            (first.get("nominal_thickness_mm") is not None, "First rotor has thickness"),
        ])
    
    # Check variety of brands
    brands = {r.get("brand") for r in autodoc_rotors if r.get("brand")}
    checks4.append((len(brands) >= 3, f"Multiple brands extracted (got {len(brands)} unique brands)"))
    
except Exception as e:
    checks4 = [(False, f"AutoDoc parser raised error: {e}")]

passed4 = sum(1 for check, _ in checks4 if check)
failed4 = len(checks4) - passed4

for check, message in checks4:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {message}")

if failed4 == 0:
    print(f"\n[PASS] Test 4 PASSED ({passed4}/{passed4} checks)")
else:
    print(f"\n[FAIL] Test 4 FAILED ({passed4}/{passed4+failed4} checks)")


# ============================================================
# Test 5: Mister-Auto list parser with fixture
# ============================================================
print("\n[TEST 5] Mister-Auto list parser - fixture extraction")
print("-" * 60)

try:
    misterauto_html = load_fixture("misterauto_list_01.html")
    misterauto_rotors = parse_rotor_list_page(misterauto_html, "mister-auto")
    
    checks5 = [
        (isinstance(misterauto_rotors, list), "Returns list"),
        (len(misterauto_rotors) >= 5, f"Extracts at least 5 rotors (got {len(misterauto_rotors)})"),
    ]
    
    # Check first rotor
    if len(misterauto_rotors) > 0:
        first = misterauto_rotors[0]
        checks5.extend([
            (first.get("brand") is not None and first.get("brand") != "", "First rotor has brand"),
            (first.get("catalog_ref") is not None and first.get("catalog_ref") != "", "First rotor has catalog_ref"),
            (first.get("outer_diameter_mm") is not None, "First rotor has diameter"),
            (first.get("nominal_thickness_mm") is not None, "First rotor has thickness"),
        ])
    
    # Check variety of brands
    brands = {r.get("brand") for r in misterauto_rotors if r.get("brand")}
    checks5.append((len(brands) >= 3, f"Multiple brands extracted (got {len(brands)} unique brands)"))
    
except Exception as e:
    checks5 = [(False, f"Mister-Auto parser raised error: {e}")]

passed5 = sum(1 for check, _ in checks5 if check)
failed5 = len(checks5) - passed5

for check, message in checks5:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {message}")

if failed5 == 0:
    print(f"\n[PASS] Test 5 PASSED ({passed5}/{passed5} checks)")
else:
    print(f"\n[FAIL] Test 5 FAILED ({passed5}/{passed5+failed5} checks)")


# ============================================================
# Test 6: PowerStop list parser with fixture
# ============================================================
print("\n[TEST 6] PowerStop list parser - fixture extraction")
print("-" * 60)

try:
    powerstop_html = load_fixture("powerstop_list_01.html")
    powerstop_rotors = parse_rotor_list_page(powerstop_html, "powerstop")
    
    checks6 = [
        (isinstance(powerstop_rotors, list), "Returns list"),
        (len(powerstop_rotors) >= 5, f"Extracts at least 5 rotors (got {len(powerstop_rotors)})"),
    ]
    
    # Check first rotor
    if len(powerstop_rotors) > 0:
        first = powerstop_rotors[0]
        checks6.extend([
            (first.get("brand") == "PowerStop", "Brand is PowerStop"),
            (first.get("catalog_ref") is not None and first.get("catalog_ref") != "", "First rotor has catalog_ref"),
            (first.get("outer_diameter_mm") is not None, "First rotor has diameter"),
            (first.get("nominal_thickness_mm") is not None, "First rotor has thickness"),
        ])
        
        # PowerStop-specific: check directionality extraction
        directional_rotors = [r for r in powerstop_rotors if r.get("directionality") in ["left", "right"]]
        checks6.append((len(directional_rotors) >= 1, f"At least one directional rotor found (got {len(directional_rotors)})"))
    
except Exception as e:
    checks6 = [(False, f"PowerStop parser raised error: {e}")]

passed6 = sum(1 for check, _ in checks6 if check)
failed6 = len(checks6) - passed6

for check, message in checks6:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {message}")

if failed6 == 0:
    print(f"\n[PASS] Test 6 PASSED ({passed6}/{passed6} checks)")
else:
    print(f"\n[FAIL] Test 6 FAILED ({passed6}/{passed6+failed6} checks)")


# ============================================================
# Test 7: Integration with normalize_rotor
# ============================================================
print("\n[TEST 7] Integration - parsed rotors compatible with normalize_rotor")
print("-" * 60)

from data_scraper.html_scraper import normalize_rotor

checks7 = []

# Test normalization of one rotor from each parser
test_rotors = []
if len(autodoc_rotors) > 0:
    test_rotors.append(("autodoc", autodoc_rotors[0]))
if len(misterauto_rotors) > 0:
    test_rotors.append(("mister-auto", misterauto_rotors[0]))
if len(powerstop_rotors) > 0:
    test_rotors.append(("powerstop", powerstop_rotors[0]))

for source, raw_rotor in test_rotors:
    try:
        normalized = normalize_rotor(raw_rotor, source=source)
        checks7.extend([
            (isinstance(normalized, dict), f"{source}: normalize_rotor returns dict"),
            (normalized.get("brand") is not None, f"{source}: Brand present after normalization"),
            (normalized.get("catalog_ref") is not None, f"{source}: Catalog ref present after normalization"),
            (normalized.get("outer_diameter_mm") is not None, f"{source}: Diameter present after normalization"),
        ])
    except Exception as e:
        checks7.append((False, f"{source}: normalize_rotor raised error: {e}"))

passed7 = sum(1 for check, _ in checks7 if check)
failed7 = len(checks7) - passed7

for check, message in checks7:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {message}")

if failed7 == 0:
    print(f"\n[PASS] Test 7 PASSED ({passed7}/{passed7} checks)")
else:
    print(f"\n[FAIL] Test 7 FAILED ({passed7}/{passed7+failed7} checks)")


# ============================================================
# Summary
# ============================================================
total_passed = passed1 + passed2 + passed3 + passed4 + passed5 + passed6 + passed7
total_failed = failed1 + failed2 + failed3 + failed4 + failed5 + failed6 + failed7

print("\n" + "="*60)
print("ALL TESTS COMPLETED")
print(f"Total: {total_passed} PASSED, {total_failed} FAILED")
print("="*60)

if total_failed == 0:
    print("\n[SUCCESS] All multi-list scraping tests passed!")
    print("\n**PRODUCTION PARSERS IMPLEMENTED:**")
    print("  - AutoDoc UK: READY")
    print("  - Mister-Auto FR: READY")
    print("  - PowerStop US: READY")
    print("\n**NOTE:** These parsers work with fixture HTML structures.")
    print("To use with real sites, replace fixtures with actual HTML from:")
    print("  - https://www.autodoc.co.uk/car-parts/brake-disc-10132")
    print("  - https://www.mister-auto.com/brake-discs/")
    print("  - https://www.powerstop.com/product-category/brake-rotors/")
else:
    print(f"\n[FAIL] {total_failed} test(s) failed")
