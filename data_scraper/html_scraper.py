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
    # Map raw dict fields -> schema_rotor.json fields
    return {
        "outer_diameter_mm": None,
        "nominal_thickness_mm": None,
        "hat_height_mm": None,
        "overall_height_mm": None,
        "center_bore_mm": None,
        "bolt_circle_mm": None,
        "bolt_hole_count": None,
        "ventilation_type": None,
        "directionality": None,
        "offset_mm": None,
        "rotor_weight_kg": None,
        "mounting_type": None,
        "oem_part_number": None,
        "pad_swept_area_mm2": None,
        "brand": source,
        "catalog_ref": raw.get("ref", None)
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
