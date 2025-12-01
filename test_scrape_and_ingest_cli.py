"""
Test suite for scrape_and_ingest.py CLI - Mission 8
Tests CLI argument parsing and routing to ingest_all without touching DB.
"""

import sys
sys.path.insert(0, '.')

import scrape_and_ingest


# Mock storage for tracking calls to ingest_all
mock_calls = []


def mock_ingest_all(group=None):
    """
    Mock replacement for database.ingest_pipeline.ingest_all.
    Records calls without executing real ingestion.
    """
    mock_calls.append({"group": group})


# Replace real ingest_all with mock
original_ingest_all = scrape_and_ingest.ingest_all
scrape_and_ingest.ingest_all = mock_ingest_all


print("="*60)
print("MISSION 8 - SCRAPE_AND_INGEST CLI TESTS")
print("="*60)


# ============================================================
# Test 1: No arguments (default behavior)
# ============================================================
print("\n[TEST 1] No arguments -> ingest all groups")
print("-" * 60)

mock_calls.clear()
scrape_and_ingest.main([])

checks1 = [
    (len(mock_calls) == 1, "ingest_all called exactly once"),
    (mock_calls[0]["group"] is None, "group parameter is None (ingest all)"),
]

passed1 = sum(1 for check, _ in checks1 if check)
failed1 = len(checks1) - passed1

print(f"Mock call recorded: {mock_calls}")
for check, message in checks1:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {message}")

if failed1 == 0:
    print(f"\n[PASS] Test 1 PASSED ({passed1}/{passed1} checks)")
else:
    print(f"\n[FAIL] Test 1 FAILED ({passed1}/{passed1+failed1} checks)")


# ============================================================
# Test 2: --only all
# ============================================================
print("\n[TEST 2] --only all -> ingest all groups")
print("-" * 60)

mock_calls.clear()
scrape_and_ingest.main(["--only", "all"])

checks2 = [
    (len(mock_calls) == 1, "ingest_all called exactly once"),
    (mock_calls[0]["group"] is None, "group parameter is None"),
]

passed2 = sum(1 for check, _ in checks2 if check)
failed2 = len(checks2) - passed2

print(f"Mock call recorded: {mock_calls}")
for check, message in checks2:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {message}")

if failed2 == 0:
    print(f"\n[PASS] Test 2 PASSED ({passed2}/{passed2} checks)")
else:
    print(f"\n[FAIL] Test 2 FAILED ({passed2}/{passed2+failed2} checks)")


# ============================================================
# Test 3: --only rotors
# ============================================================
print("\n[TEST 3] --only rotors -> ingest rotors only")
print("-" * 60)

mock_calls.clear()
scrape_and_ingest.main(["--only", "rotors"])

checks3 = [
    (len(mock_calls) == 1, "ingest_all called exactly once"),
    (mock_calls[0]["group"] == "rotors", "group parameter is 'rotors'"),
]

passed3 = sum(1 for check, _ in checks3 if check)
failed3 = len(checks3) - passed3

print(f"Mock call recorded: {mock_calls}")
for check, message in checks3:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {message}")

if failed3 == 0:
    print(f"\n[PASS] Test 3 PASSED ({passed3}/{passed3} checks)")
else:
    print(f"\n[FAIL] Test 3 FAILED ({passed3}/{passed3+failed3} checks)")


# ============================================================
# Test 4: --only pads
# ============================================================
print("\n[TEST 4] --only pads -> ingest pads only")
print("-" * 60)

mock_calls.clear()
scrape_and_ingest.main(["--only", "pads"])

checks4 = [
    (len(mock_calls) == 1, "ingest_all called exactly once"),
    (mock_calls[0]["group"] == "pads", "group parameter is 'pads'"),
]

passed4 = sum(1 for check, _ in checks4 if check)
failed4 = len(checks4) - passed4

print(f"Mock call recorded: {mock_calls}")
for check, message in checks4:
    status = "[PASS]" if check else "[FAIL]"
    print(f"{status} {message}")

if failed4 == 0:
    print(f"\n[PASS] Test 4 PASSED ({passed4}/{passed4} checks)")
else:
    print(f"\n[FAIL] Test 4 FAILED ({passed4}/{passed4+failed4} checks)")


# ============================================================
# Test 5: --only vehicles
# ============================================================
print("\n[TEST 5] --only vehicles -> ingest vehicles only")
print("-" * 60)

mock_calls.clear()
scrape_and_ingest.main(["--only", "vehicles"])

checks5 = [
    (len(mock_calls) == 1, "ingest_all called exactly once"),
    (mock_calls[0]["group"] == "vehicles", "group parameter is 'vehicles'"),
]

passed5 = sum(1 for check, _ in checks5 if check)
failed5 = len(checks5) - passed5

print(f"Mock call recorded: {mock_calls}")
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
    print("\n[SUCCESS] All CLI tests passed!")
    print("\nThe CLI correctly routes arguments to ingest_all:")
    print("  - No args / --only all -> group=None")
    print("  - --only rotors -> group='rotors'")
    print("  - --only pads -> group='pads'")
    print("  - --only vehicles -> group='vehicles'")
else:
    print(f"\n[FAIL] {total_failed} test(s) failed")

# Restore original function (cleanup)
scrape_and_ingest.ingest_all = original_ingest_all
