# database/ingest_pipeline.py

import csv
import json
import os
import sqlite3
import sys
from pathlib import Path

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data_scraper.html_scraper import (
    fetch_html,
    parse_dba_rotor_page,
    normalize_rotor,
    parse_ebc_pad_page,
    normalize_pad,
    parse_wheelsize_vehicle_page,
    normalize_vehicle
)

DB_PATH = "database/bbk.db"
SEED_INDEX_PATH = "data_seed_url.txt"

def insert_rotor(conn, rotor: dict):
    fields = ",".join(rotor.keys())
    placeholders = ",".join(["?"] * len(rotor))
    sql = f"INSERT INTO rotors ({fields}) VALUES ({placeholders})"
    conn.execute(sql, list(rotor.values()))

def insert_pad(conn, pad: dict):
    fields = ",".join(pad.keys())
    placeholders = ",".join(["?"] * len(pad))
    sql = f"INSERT INTO pads ({fields}) VALUES ({placeholders})"
    conn.execute(sql, list(pad.values()))

def insert_vehicle(conn, vh: dict):
    fields = ",".join(vh.keys())
    placeholders = ",".join(["?"] * len(vh))
    sql = f"INSERT INTO vehicles ({fields}) VALUES ({placeholders})"
    conn.execute(sql, list(vh.values()))

def ingest_jsonl(path: str, table: str):
    conn = sqlite3.connect(DB_PATH)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            if table == "rotors":
                insert_rotor(conn, obj)
            elif table == "pads":
                insert_pad(conn, obj)
            elif table == "vehicles":
                insert_vehicle(conn, obj)
    conn.commit()
    conn.close()

# ------------------------------------------------------------
#  Seed Loading Helpers
# ------------------------------------------------------------

def load_seed_csv_paths() -> dict:
    """
    Parse data_seed_url.txt and extract CSV paths for each group.
    
    Returns:
        dict: {"rotors": [paths], "pads": [paths], "vehicles": [paths]}
    """
    paths = {"rotors": [], "pads": [], "vehicles": []}
    
    if not os.path.exists(SEED_INDEX_PATH):
        return paths
    
    with open(SEED_INDEX_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Look for CSV file paths
            if ".csv" in line:
                # Extract path (format: "path/to/file.csv" or just path)
                parts = line.split()
                for part in parts:
                    if ".csv" in part:
                        csv_path = part.strip(",;")
                        
                        # Determine group from filename
                        if "rotors" in csv_path:
                            paths["rotors"].append(csv_path)
                        elif "pads" in csv_path:
                            paths["pads"].append(csv_path)
                        elif "vehicles" in csv_path:
                            paths["vehicles"].append(csv_path)
                        break
    
    return paths

def iter_seed_urls(kind: str):
    """
    Iterate over all URLs for a given group (rotors, pads, or vehicles).
    
    Args:
        kind: One of "rotors", "pads", "vehicles"
    
    Yields:
        tuple: (source, url, notes)
    """
    paths = load_seed_csv_paths()
    csv_paths = paths.get(kind, [])
    
    for csv_path in csv_paths:
        if not os.path.exists(csv_path):
            print(f"[WARNING] CSV not found: {csv_path}")
            continue
        
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                source = row.get("source", "").strip()
                url = row.get("url", "").strip()
                notes = row.get("notes", "").strip()
                
                if source and url:
                    yield (source, url, notes)

# ------------------------------------------------------------
#  Processing Functions
# ------------------------------------------------------------

def process_rotor_seed(conn, source: str, url: str) -> int:
    """
    Fetch, parse, normalize and insert rotor data from a single URL.
    
    Returns:
        int: Number of rotors inserted
    """
    try:
        print(f"[ROTOR] Fetching {source}: {url}")
        html = fetch_html(url)
        
        # parse_dba_rotor_page returns already normalized dict
        rotor = parse_dba_rotor_page(html)
        
        # Validate required fields
        if not rotor or not isinstance(rotor, dict):
            print(f"[ROTOR] Invalid result from parser")
            return 0
        
        required_fields = ["outer_diameter_mm", "nominal_thickness_mm", "brand", "catalog_ref"]
        if not all(rotor.get(f) for f in required_fields):
            print(f"[ROTOR] Missing required fields")
            return 0
        
        insert_rotor(conn, rotor)
        print(f"[ROTOR] ✓ Inserted: {rotor.get('brand')} {rotor.get('catalog_ref')}")
        return 1
        
    except Exception as e:
        print(f"[ROTOR] ✗ Error processing {url}: {e}")
        return 0

def process_pad_seed(conn, source: str, url: str) -> int:
    """
    Fetch, parse, normalize and insert pad data from a single URL.
    
    Returns:
        int: Number of pads inserted
    """
    try:
        print(f"[PAD] Fetching {source}: {url}")
        html = fetch_html(url)
        
        # parse_ebc_pad_page returns already normalized dict
        pad = parse_ebc_pad_page(html)
        
        # Validate required fields
        if not pad or not isinstance(pad, dict):
            print(f"[PAD] Invalid result from parser")
            return 0
        
        required_fields = ["shape_id", "length_mm", "height_mm", "thickness_mm", "brand", "catalog_ref"]
        if not all(pad.get(f) for f in required_fields):
            print(f"[PAD] Missing required fields")
            return 0
        
        insert_pad(conn, pad)
        print(f"[PAD] ✓ Inserted: {pad.get('brand')} {pad.get('catalog_ref')}")
        return 1
        
    except Exception as e:
        print(f"[PAD] ✗ Error processing {url}: {e}")
        return 0

def process_vehicle_seed(conn, source: str, url: str) -> int:
    """
    Fetch, parse, normalize and insert vehicle data from a single URL.
    
    Returns:
        int: Number of vehicles inserted
    """
    try:
        print(f"[VEHICLE] Fetching {source}: {url}")
        html = fetch_html(url)
        
        # parse_wheelsize_vehicle_page returns RAW dict
        raw = parse_wheelsize_vehicle_page(html)
        
        if not raw or not isinstance(raw, dict):
            print(f"[VEHICLE] Invalid result from parser")
            return 0
        
        # Normalize
        vehicle = normalize_vehicle(raw, source="wheelsize")
        
        # Validate required fields
        required_fields = ["make", "model", "year_from", "hub_bolt_circle_mm", 
                          "hub_bolt_hole_count", "hub_center_bore_mm"]
        if not all(vehicle.get(f) for f in required_fields):
            print(f"[VEHICLE] Missing required fields")
            return 0
        
        insert_vehicle(conn, vehicle)
        print(f"[VEHICLE] ✓ Inserted: {vehicle.get('make')} {vehicle.get('model')} "
              f"({vehicle.get('year_from')}-{vehicle.get('year_to') or 'now'})")
        return 1
        
    except Exception as e:
        print(f"[VEHICLE] ✗ Error processing {url}: {e}")
        return 0

# ------------------------------------------------------------
#  Main Ingestion Pipeline
# ------------------------------------------------------------

def ingest_all(group: str | None = None) -> None:
    """
    Main ingestion pipeline that reads seed URLs and populates the database.
    
    Args:
        group: Optional filter - one of "rotors", "pads", "vehicles".
               If None, processes all groups.
    """
    print("="*60)
    print("BIGBRAKEKIT - INGESTION PIPELINE")
    print("="*60)
    
    # Validate group parameter
    valid_groups = ["rotors", "pads", "vehicles"]
    groups_to_process = valid_groups if group is None else [group]
    
    if group and group not in valid_groups:
        print(f"[ERROR] Invalid group '{group}'. Must be one of: {valid_groups}")
        return
    
    # Initialize database connection
    conn = sqlite3.connect(DB_PATH)
    
    # Track statistics
    stats = {"rotors": 0, "pads": 0, "vehicles": 0, "errors": 0}
    
    try:
        # Process each group
        for current_group in groups_to_process:
            print(f"\n{'='*60}")
            print(f"Processing {current_group.upper()}")
            print(f"{'='*60}")
            
            group_count = 0
            
            for source, url, notes in iter_seed_urls(current_group):
                if notes:
                    print(f"\nNote: {notes}")
                
                # Call appropriate processor
                if current_group == "rotors":
                    count = process_rotor_seed(conn, source, url)
                elif current_group == "pads":
                    count = process_pad_seed(conn, source, url)
                elif current_group == "vehicles":
                    count = process_vehicle_seed(conn, source, url)
                else:
                    count = 0
                
                group_count += count
                if count == 0:
                    stats["errors"] += 1
            
            stats[current_group] = group_count
            print(f"\n{current_group.upper()} Summary: {group_count} inserted")
        
        # Commit all changes
        conn.commit()
        print(f"\n{'='*60}")
        print("INGESTION COMPLETE")
        print(f"{'='*60}")
        print(f"Rotors inserted:   {stats['rotors']}")
        print(f"Pads inserted:     {stats['pads']}")
        print(f"Vehicles inserted: {stats['vehicles']}")
        print(f"Errors encountered: {stats['errors']}")
        print("="*60)
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

# ------------------------------------------------------------
#  CLI Entry Point
# ------------------------------------------------------------

if __name__ == "__main__":
    import sys
    
    # Simple CLI: python -m database.ingest_pipeline [group]
    group_arg = sys.argv[1] if len(sys.argv) > 1 else None
    ingest_all(group=group_arg)
