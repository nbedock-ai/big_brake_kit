# rotor_analysis/clustering.py
"""
Rotor clustering module for BigBrakeKit (Mission 10).

Performs preliminary geometric clustering of rotors from the database using binning strategy.
Groups rotors by (outer_diameter, nominal_thickness, offset) for master rotor selection (M11).

This is a V1 implementation using simple binning, not k-means or advanced clustering.
"""

import json
import os
import sqlite3
from typing import Optional

# Constants
DB_PATH = "database/bbk.db"

# Binning steps for clustering dimensions (in mm)
DIAM_BIN_STEP_MM = 5.0        # Group rotors within 5mm diameter range
THICK_BIN_STEP_MM = 0.5       # Group rotors within 0.5mm thickness range
OFFSET_BIN_STEP_MM = 2.0      # Group rotors within 2mm offset range


def load_rotors_from_db(db_path: str = DB_PATH) -> list[dict]:
    """
    Load all rotors from SQLite database.
    
    Args:
        db_path: Path to SQLite database file
    
    Returns:
        List of rotor dicts with all columns from the rotors table
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    
    try:
        cursor = conn.execute("""
            SELECT 
                outer_diameter_mm,
                nominal_thickness_mm,
                hat_height_mm,
                overall_height_mm,
                offset_mm,
                center_bore_mm,
                bolt_circle_mm,
                bolt_hole_count,
                ventilation_type,
                directionality,
                rotor_weight_kg,
                mounting_type,
                brand,
                catalog_ref
            FROM rotors
        """)
        
        rotors = [dict(row) for row in cursor.fetchall()]
        return rotors
    finally:
        conn.close()


def effective_offset_mm(rotor: dict) -> Optional[float]:
    """
    Calculate effective offset for a rotor.
    
    Strategy:
    1. If offset_mm is explicitly provided → use it
    2. Otherwise, if overall_height_mm and hat_height_mm are available:
       offset = overall_height_mm - hat_height_mm
    3. Otherwise → return None (cannot determine offset)
    
    Args:
        rotor: Rotor dict with geometry fields
    
    Returns:
        Effective offset in mm, or None if cannot be determined
    """
    # Strategy 1: Explicit offset
    if rotor.get("offset_mm") is not None:
        return float(rotor["offset_mm"])
    
    # Strategy 2: Calculate from overall and hat heights
    overall = rotor.get("overall_height_mm")
    hat = rotor.get("hat_height_mm")
    
    if overall is not None and hat is not None:
        return float(overall) - float(hat)
    
    # Strategy 3: Cannot determine
    return None


def bin_value(x: float, step: float) -> float:
    """
    Round a value to the nearest bin center.
    
    Example: bin_value(282.3, 5.0) → 280.0
             bin_value(287.8, 5.0) → 290.0
    
    Args:
        x: Value to bin
        step: Bin step size
    
    Returns:
        Binned value (rounded to nearest multiple of step)
    """
    return round(x / step) * step


def compute_cluster_key(rotor: dict) -> Optional[tuple[float, float, float]]:
    """
    Compute cluster key for a rotor based on geometric binning.
    
    Clustering dimensions:
    - outer_diameter_mm (binned to DIAM_BIN_STEP_MM)
    - nominal_thickness_mm (binned to THICK_BIN_STEP_MM)
    - effective offset (binned to OFFSET_BIN_STEP_MM)
    
    Args:
        rotor: Rotor dict with geometry fields
    
    Returns:
        Tuple of (diam_bin, thick_bin, offset_bin), or None if any dimension is missing
    """
    # Extract required dimensions
    outer_diam = rotor.get("outer_diameter_mm")
    thickness = rotor.get("nominal_thickness_mm")
    offset_eff = effective_offset_mm(rotor)
    
    # Skip rotors with missing critical dimensions
    if outer_diam is None or thickness is None or offset_eff is None:
        return None
    
    # Bin each dimension
    diam_bin = bin_value(float(outer_diam), DIAM_BIN_STEP_MM)
    thick_bin = bin_value(float(thickness), THICK_BIN_STEP_MM)
    offset_bin = bin_value(offset_eff, OFFSET_BIN_STEP_MM)
    
    return (diam_bin, thick_bin, offset_bin)


def build_clusters(rotors: list[dict]) -> dict:
    """
    Build clusters from rotor list using geometric binning.
    
    Algorithm:
    1. For each rotor, compute cluster key (binned geometry)
    2. Group rotors with same key into clusters
    3. Calculate centroid (mean) for each cluster
    
    Args:
        rotors: List of rotor dicts from database
    
    Returns:
        Dict mapping cluster_key → cluster data:
        {
            (diam, thick, offset): {
                "members": [{brand, catalog_ref, ...}, ...],
                "centroid": {outer_diameter_mm, nominal_thickness_mm, offset_mm},
                "count": int
            }
        }
    """
    clusters = {}
    
    for rotor in rotors:
        # Compute cluster key
        key = compute_cluster_key(rotor)
        if key is None:
            continue  # Skip rotors with incomplete geometry
        
        # Initialize cluster if first member
        if key not in clusters:
            clusters[key] = {
                "members": [],
                "sum_diameter": 0.0,
                "sum_thickness": 0.0,
                "sum_offset": 0.0,
                "count": 0,
            }
        
        # Add rotor to cluster
        offset_eff = effective_offset_mm(rotor)
        member = {
            "brand": rotor.get("brand"),
            "catalog_ref": rotor.get("catalog_ref"),
            "outer_diameter_mm": rotor.get("outer_diameter_mm"),
            "nominal_thickness_mm": rotor.get("nominal_thickness_mm"),
            "offset_mm": offset_eff,
        }
        
        clusters[key]["members"].append(member)
        clusters[key]["sum_diameter"] += rotor["outer_diameter_mm"]
        clusters[key]["sum_thickness"] += rotor["nominal_thickness_mm"]
        clusters[key]["sum_offset"] += offset_eff
        clusters[key]["count"] += 1
    
    # Calculate centroids
    for key, cluster in clusters.items():
        count = cluster["count"]
        cluster["centroid"] = {
            "outer_diameter_mm": cluster["sum_diameter"] / count,
            "nominal_thickness_mm": cluster["sum_thickness"] / count,
            "offset_mm": cluster["sum_offset"] / count,
        }
        
        # Clean up temporary sum fields
        del cluster["sum_diameter"]
        del cluster["sum_thickness"]
        del cluster["sum_offset"]
    
    return clusters


def clusters_to_json_serializable(clusters: dict) -> dict:
    """
    Convert clusters dict to JSON-serializable format.
    
    Transforms tuple keys into structured objects with metadata.
    
    Args:
        clusters: Clusters dict from build_clusters()
    
    Returns:
        JSON-serializable dict with meta info and cluster list
    """
    output = {
        "meta": {
            "diam_bin_step_mm": DIAM_BIN_STEP_MM,
            "thick_bin_step_mm": THICK_BIN_STEP_MM,
            "offset_bin_step_mm": OFFSET_BIN_STEP_MM,
            "cluster_count": len(clusters),
        },
        "clusters": [],
    }
    
    # Convert each cluster to JSON-friendly format
    for idx, (key, cluster) in enumerate(clusters.items()):
        diam_bin, thick_bin, offset_bin = key
        
        cluster_obj = {
            "cluster_id": idx,
            "key": {
                "outer_diameter_mm": diam_bin,
                "nominal_thickness_mm": thick_bin,
                "offset_mm": offset_bin,
            },
            "centroid": cluster["centroid"],
            "count": cluster["count"],
            "members": cluster["members"],
        }
        
        output["clusters"].append(cluster_obj)
    
    return output


def run_clustering(db_path: str = DB_PATH, output_path: str = "rotor_analysis/rotor_clusters.json") -> None:
    """
    Main function to run complete clustering pipeline.
    
    Steps:
    1. Load rotors from database
    2. Build geometric clusters
    3. Convert to JSON format
    4. Write to output file
    
    Args:
        db_path: Path to SQLite database
        output_path: Path for output JSON file
    """
    print("="*60)
    print("ROTOR CLUSTERING ANALYSIS (M10)")
    print("="*60)
    
    # Step 1: Load rotors
    print(f"\n[1/4] Loading rotors from {db_path}...")
    rotors = load_rotors_from_db(db_path)
    print(f"      Loaded {len(rotors)} rotors")
    
    # Step 2: Build clusters
    print(f"\n[2/4] Building clusters (binning strategy)...")
    print(f"      Diameter bins: {DIAM_BIN_STEP_MM}mm")
    print(f"      Thickness bins: {THICK_BIN_STEP_MM}mm")
    print(f"      Offset bins: {OFFSET_BIN_STEP_MM}mm")
    clusters = build_clusters(rotors)
    print(f"      Created {len(clusters)} clusters")
    
    # Step 3: Convert to JSON
    print(f"\n[3/4] Converting to JSON format...")
    data = clusters_to_json_serializable(clusters)
    
    # Count total rotors in clusters (some may be skipped if incomplete)
    total_clustered = sum(c["count"] for c in data["clusters"])
    print(f"      {total_clustered} rotors clustered ({len(rotors) - total_clustered} skipped)")
    
    # Step 4: Write output
    print(f"\n[4/4] Writing output to {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"      Output written successfully")
    
    # Summary
    print("\n" + "="*60)
    print("CLUSTERING COMPLETE")
    print("="*60)
    print(f"Total rotors:     {len(rotors)}")
    print(f"Clustered:        {total_clustered}")
    print(f"Skipped:          {len(rotors) - total_clustered}")
    print(f"Clusters created: {len(clusters)}")
    print(f"Output file:      {output_path}")
    print("="*60)


if __name__ == "__main__":
    run_clustering()
