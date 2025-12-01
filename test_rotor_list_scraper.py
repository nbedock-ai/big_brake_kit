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
# Test 4: parse_rotor_list_page - template parsers
# ============================================================
print("\n[TEST 4] parse_rotor_list_page - template parsers return lists")
print("-" * 60)

# Test that template parsers return lists (even if empty, since they're templates)
template_sources = ["autodoc", "mister-auto", "powerstop"]
checks4 = []

for source in template_sources:
    try:
        result = parse_rotor_list_page("<html>test</html>", source)
        is_list = isinstance(result, list)
        checks4.append((is_list, f"{source} parser returns list (got {type(result).__name__})"))
    except Exception as e:
        checks4.append((False, f"{source} parser raised unexpected error: {e}"))

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
# Test 5: Integration with normalize_rotor
# ============================================================
print("\n[TEST 5] Integration - raw dict compatible with normalize_rotor")
print("-" * 60)

# Create a mock raw rotor dict as would be returned by parse_rotor_list_page
from data_scraper.html_scraper import normalize_rotor

raw_rotor = {
    "brand_raw": "Bosch",
    "catalog_ref_raw": "0986479123",
    "outer_diameter_mm_raw": 280.0,
    "nominal_thickness_mm_raw": 22.0,
    "source": "test"
}

try:
    normalized = normalize_rotor(raw_rotor, source="test")
    checks5 = [
        (isinstance(normalized, dict), "normalize_rotor returns dict"),
        (normalized.get("brand") is not None, "Brand field present after normalization"),
        (normalized.get("catalog_ref") is not None, "Catalog ref present after normalization"),
    ]
except Exception as e:
    checks5 = [(False, f"normalize_rotor raised error: {e}")]

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
# Summary
# ============================================================
total_passed = passed1 + passed2 + passed3 + passed4 + passed5
total_failed = failed1 + failed2 + failed3 + failed4 + failed5

print("\n" + "="*60)
print("ALL TESTS COMPLETED")
print(f"Total: {total_passed} PASSED, {total_failed} FAILED")
print("="*60)

if total_failed == 0:
    print("\n[SUCCESS] All multi-list scraping tests passed!")
    print("\n**NOTE:** Template parsers require manual implementation.")
    print("See html_rotor_list_scraper.py TODOs for site-specific parsing.")
else:
    print(f"\n[FAIL] {total_failed} test(s) failed")
