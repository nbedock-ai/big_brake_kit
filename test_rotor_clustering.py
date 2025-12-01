"""
Test suite for rotor clustering (Mission 10).
Tests binning logic, cluster building, and JSON serialization.
"""

import sys
sys.path.insert(0, '.')

from rotor_analysis.clustering import (
    effective_offset_mm,
    bin_value,
    compute_cluster_key,
    build_clusters,
    clusters_to_json_serializable,
    DIAM_BIN_STEP_MM,
    THICK_BIN_STEP_MM,
    OFFSET_BIN_STEP_MM,
)

print("="*60)
print("MISSION 10 - ROTOR CLUSTERING TESTS")
print("="*60)


# ============================================================
# Test 1: Binning function
# ============================================================
print("\n[TEST 1] bin_value() - geometric binning")
print("-" * 60)

checks1 = [
    (bin_value(282.3, 5.0) == 280.0, "282.3mm -> 280mm bin (step=5)"),
    (bin_value(287.8, 5.0) == 290.0, "287.8mm -> 290mm bin (step=5)"),
    (bin_value(22.4, 0.5) == 22.5, "22.4mm -> 22.5mm bin (step=0.5)"),
    (bin_value(22.2, 0.5) == 22.0, "22.2mm -> 22.0mm bin (step=0.5)"),
    (bin_value(45, 2.0) == 44.0, "45mm -> 44mm bin (step=2, rounds down)"),
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
# Test 2: Effective offset calculation
# ============================================================
print("\n[TEST 2] effective_offset_mm() - offset strategies")
print("-" * 60)

# Case 1: Explicit offset
rotor_explicit = {"offset_mm": 42.5}
offset1 = effective_offset_mm(rotor_explicit)

# Case 2: Calculated from heights
rotor_calculated = {
    "offset_mm": None,
    "overall_height_mm": 50.0,
    "hat_height_mm": 10.0
}
offset2 = effective_offset_mm(rotor_calculated)

# Case 3: Cannot determine
rotor_incomplete = {
    "offset_mm": None,
    "overall_height_mm": None,
    "hat_height_mm": 10.0
}
offset3 = effective_offset_mm(rotor_incomplete)

checks2 = [
    (offset1 == 42.5, "Explicit offset_mm=42.5 -> 42.5"),
    (offset2 == 40.0, "overall(50) - hat(10) -> 40.0"),
    (offset3 is None, "Incomplete data -> None"),
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
# Test 3: Cluster key computation
# ============================================================
print("\n[TEST 3] compute_cluster_key() - key generation")
print("-" * 60)

# Case 1: Complete rotor
rotor_complete = {
    "outer_diameter_mm": 282.3,
    "nominal_thickness_mm": 22.4,
    "offset_mm": 45.0,
}
key1 = compute_cluster_key(rotor_complete)

# Case 2: Calculated offset
rotor_calc_offset = {
    "outer_diameter_mm": 300.0,
    "nominal_thickness_mm": 24.0,
    "offset_mm": None,
    "overall_height_mm": 50.0,
    "hat_height_mm": 10.0,
}
key2 = compute_cluster_key(rotor_calc_offset)

# Case 3: Incomplete (missing diameter)
rotor_incomplete2 = {
    "outer_diameter_mm": None,
    "nominal_thickness_mm": 22.0,
    "offset_mm": 40.0,
}
key3 = compute_cluster_key(rotor_incomplete2)

checks3 = [
    (key1 == (280.0, 22.5, 44.0), "Complete rotor -> binned key (280, 22.5, 44)"),
    (key2 == (300.0, 24.0, 40.0), "Calculated offset -> binned key (300, 24, 40)"),
    (key3 is None, "Incomplete rotor -> None"),
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
# Test 4: Cluster building
# ============================================================
print("\n[TEST 4] build_clusters() - grouping and centroids")
print("-" * 60)

# Create synthetic rotor dataset
test_rotors = [
    # Cluster 1: Two rotors very close (same bin)
    {
        "brand": "DBA",
        "catalog_ref": "DBA2000",
        "outer_diameter_mm": 280.0,
        "nominal_thickness_mm": 22.0,
        "offset_mm": 40.0,
        "hat_height_mm": 30.0,
        "overall_height_mm": 70.0,
    },
    {
        "brand": "DBA",
        "catalog_ref": "DBA2001",
        "outer_diameter_mm": 282.0,  # Same bin (280)
        "nominal_thickness_mm": 22.2,  # Same bin (22.0)
        "offset_mm": 41.0,  # Same bin (40)
        "hat_height_mm": 31.0,
        "overall_height_mm": 72.0,
    },
    # Cluster 2: One rotor different diameter
    {
        "brand": "Brembo",
        "catalog_ref": "BRM3000",
        "outer_diameter_mm": 300.0,  # Different bin (300)
        "nominal_thickness_mm": 24.0,  # Different bin (24.0)
        "offset_mm": 42.0,  # Different bin (42)
        "hat_height_mm": 32.0,
        "overall_height_mm": 74.0,
    },
    # Incomplete rotor (should be skipped)
    {
        "brand": "Skip",
        "catalog_ref": "SKIP001",
        "outer_diameter_mm": None,  # Missing
        "nominal_thickness_mm": 20.0,
        "offset_mm": 38.0,
        "hat_height_mm": 30.0,
        "overall_height_mm": 68.0,
    },
]

clusters = build_clusters(test_rotors)

# Verify cluster structure
cluster_count = len(clusters)
cluster1_key = (280.0, 22.0, 40.0)
cluster2_key = (300.0, 24.0, 42.0)

has_cluster1 = cluster1_key in clusters
has_cluster2 = cluster2_key in clusters

if has_cluster1:
    c1_count = clusters[cluster1_key]["count"]
    c1_members = clusters[cluster1_key]["members"]
    c1_centroid = clusters[cluster1_key]["centroid"]
    c1_has_centroid = "outer_diameter_mm" in c1_centroid
else:
    c1_count = 0
    c1_has_centroid = False

if has_cluster2:
    c2_count = clusters[cluster2_key]["count"]
else:
    c2_count = 0

checks4 = [
    (cluster_count == 2, f"Two clusters created (got {cluster_count})"),
    (has_cluster1, "Cluster 1 exists (280, 22, 40)"),
    (has_cluster2, "Cluster 2 exists (300, 24, 42)"),
    (c1_count == 2, f"Cluster 1 has 2 members (got {c1_count})"),
    (c2_count == 1, f"Cluster 2 has 1 member (got {c2_count})"),
    (c1_has_centroid, "Cluster 1 has centroid with diameter field"),
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


# ============================================================
# Test 5: JSON serialization
# ============================================================
print("\n[TEST 5] clusters_to_json_serializable() - format conversion")
print("-" * 60)

# Use clusters from Test 4
json_data = clusters_to_json_serializable(clusters)

has_meta = "meta" in json_data
has_clusters = "clusters" in json_data

if has_meta:
    has_diam_step = "diam_bin_step_mm" in json_data["meta"]
    cluster_count_meta = json_data["meta"].get("cluster_count")
else:
    has_diam_step = False
    cluster_count_meta = 0

if has_clusters and len(json_data["clusters"]) > 0:
    first_cluster = json_data["clusters"][0]
    has_cluster_id = "cluster_id" in first_cluster
    has_key = "key" in first_cluster
    has_centroid = "centroid" in first_cluster
    has_count = "count" in first_cluster
    has_members = "members" in first_cluster
else:
    has_cluster_id = has_key = has_centroid = has_count = has_members = False

checks5 = [
    (has_meta, "JSON has 'meta' field"),
    (has_clusters, "JSON has 'clusters' field"),
    (has_diam_step, "Meta contains bin step info"),
    (cluster_count_meta == 2, f"Meta cluster_count=2 (got {cluster_count_meta})"),
    (has_cluster_id, "Cluster has 'cluster_id'"),
    (has_key, "Cluster has 'key' dict"),
    (has_centroid, "Cluster has 'centroid' dict"),
    (has_count, "Cluster has 'count'"),
    (has_members, "Cluster has 'members' list"),
]

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
    print("\n[SUCCESS] All clustering tests passed!")
    print("\nClustering algorithm validated:")
    print(f"  - Binning: {DIAM_BIN_STEP_MM}mm / {THICK_BIN_STEP_MM}mm / {OFFSET_BIN_STEP_MM}mm")
    print("  - Offset calculation: explicit and fallback strategies")
    print("  - Cluster key generation: 3D geometric binning")
    print("  - Cluster building: grouping and centroid calculation")
    print("  - JSON serialization: structured output format")
else:
    print(f"\n[FAIL] {total_failed} test(s) failed")
