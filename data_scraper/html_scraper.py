# data_scraper/html_scraper.py

import requests
from bs4 import BeautifulSoup

# ------------------------------------------------------------
#  Fetch
# ------------------------------------------------------------

def fetch_html(url: str) -> str:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.text

# ------------------------------------------------------------
#  Parsing — DBA Rotors
# ------------------------------------------------------------

def parse_dba_rotor_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # TODO: Extract table rows / spec blocks
    # Each result must map raw fields (strings) with minimal cleanup.
    return results

# ------------------------------------------------------------
#  Parsing — Brembo Rotors
# ------------------------------------------------------------

def parse_brembo_rotor_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # TODO: Extract HTML table of rotor specs.
    return results

# ------------------------------------------------------------
#  Parsing — EBC Pads
# ------------------------------------------------------------

def parse_ebc_pad_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # TODO: Extract pad shape dimensions.
    return results

# ------------------------------------------------------------
#  Parsing — Wheel-Size Vehicle Fitment
# ------------------------------------------------------------

def parse_wheelsize_vehicle_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # TODO: Extract PCD, center bore, OEM rotor specs.
    return results

# ------------------------------------------------------------
#  Normalization
# ------------------------------------------------------------

def normalize_rotor(raw: dict, source: str) -> dict:
    """
    Normalize raw rotor data to conform to schema_rotor.json.
    
    Args:
        raw: Dict with raw string/numeric values from scraper
        source: Brand/source identifier (e.g., 'dba', 'brembo')
    
    Returns:
        Dict conforming to RotorSpec schema
    """
    def safe_float(val):
        """Convert to float, return None if not possible."""
        if val is None or val == "":
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
    
    def safe_int(val):
        """Convert to int, return None if not possible."""
        if val is None or val == "":
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None
    
    # Parse required numeric fields
    outer_diameter_mm = safe_float(raw.get("outer_diameter_mm"))
    nominal_thickness_mm = safe_float(raw.get("nominal_thickness_mm"))
    hat_height_mm = safe_float(raw.get("hat_height_mm"))
    overall_height_mm = safe_float(raw.get("overall_height_mm"))
    center_bore_mm = safe_float(raw.get("center_bore_mm"))
    bolt_circle_mm = safe_float(raw.get("bolt_circle_mm"))
    bolt_hole_count = safe_int(raw.get("bolt_hole_count"))
    
    # Standardize ventilation_type (must be in enum)
    ventilation_raw = raw.get("ventilation_type", "").lower()
    ventilation_map = {
        "solid": "solid",
        "vented": "vented",
        "drilled": "drilled",
        "slotted": "slotted",
        "drilled_slotted": "drilled_slotted",
        "drilled/slotted": "drilled_slotted",
        "drilled and slotted": "drilled_slotted"
    }
    ventilation_type = ventilation_map.get(ventilation_raw, "vented")
    
    # Standardize directionality (must be in enum)
    directionality_raw = raw.get("directionality", "").lower()
    directionality_map = {
        "non_directional": "non_directional",
        "non-directional": "non_directional",
        "left": "left",
        "right": "right",
        "l": "left",
        "r": "right"
    }
    directionality = directionality_map.get(directionality_raw, "non_directional")
    
    # Calculate offset_mm if not provided
    offset_mm = safe_float(raw.get("offset_mm"))
    if offset_mm is None and overall_height_mm is not None and hat_height_mm is not None:
        offset_mm = overall_height_mm - hat_height_mm
    
    # Parse optional fields
    rotor_weight_kg = safe_float(raw.get("rotor_weight_kg"))
    pad_swept_area_mm2 = safe_float(raw.get("pad_swept_area_mm2"))
    
    # Mounting type (must be in enum or None)
    mounting_type_raw = raw.get("mounting_type", "").lower().replace(" ", "_")
    mounting_map = {
        "1_piece": "1_piece",
        "2_piece_bolted": "2_piece_bolted",
        "2_piece_floating": "2_piece_floating",
        "2-piece_bolted": "2_piece_bolted",
        "2-piece_floating": "2_piece_floating"
    }
    mounting_type = mounting_map.get(mounting_type_raw, None)
    
    # OEM part number (optional string)
    oem_part_number = raw.get("oem_part_number", None)
    
    # Brand and catalog ref
    brand = source
    catalog_ref = raw.get("ref") or raw.get("catalog_ref") or ""
    
    return {
        "outer_diameter_mm": outer_diameter_mm,
        "nominal_thickness_mm": nominal_thickness_mm,
        "hat_height_mm": hat_height_mm,
        "overall_height_mm": overall_height_mm,
        "center_bore_mm": center_bore_mm,
        "bolt_circle_mm": bolt_circle_mm,
        "bolt_hole_count": bolt_hole_count,
        "ventilation_type": ventilation_type,
        "directionality": directionality,
        "offset_mm": offset_mm,
        "rotor_weight_kg": rotor_weight_kg,
        "mounting_type": mounting_type,
        "oem_part_number": oem_part_number,
        "pad_swept_area_mm2": pad_swept_area_mm2,
        "brand": brand,
        "catalog_ref": catalog_ref
    }

def normalize_pad(raw: dict, source: str) -> dict:
    return {
        "shape_id": raw.get("shape_id"),
        "length_mm": None,
        "height_mm": None,
        "thickness_mm": None,
        "swept_area_mm2": None,
        "backing_plate_type": None,
        "brand": source,
        "catalog_ref": raw.get("ref", None)
    }

def normalize_vehicle(raw: dict, source: str) -> dict:
    return {
        "make": raw.get("make"),
        "model": raw.get("model"),
        "generation": raw.get("generation"),
        "year_from": raw.get("year_from"),
        "year_to": raw.get("year_to"),
        "hub_bolt_circle_mm": None,
        "hub_bolt_hole_count": None,
        "hub_center_bore_mm": None,
        "knuckle_bolt_spacing_mm": None,
        "knuckle_bolt_orientation_deg": None,
        "max_rotor_diameter_mm": None,
        "wheel_inner_barrel_clearance_mm": None,
        "rotor_thickness_min_mm": None,
        "rotor_thickness_max_mm": None
    }
