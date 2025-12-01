# data_scraper/html_scraper.py

import re
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

def parse_dba_rotor_page(html: str) -> dict:
    """
    Parse a DBA rotor product page and extract rotor specifications.
    
    Args:
        html: HTML content of a DBA rotor product page
    
    Returns:
        Normalized rotor dict conforming to schema_rotor.json
    """
    soup = BeautifulSoup(html, "html.parser")
    raw = {}
    
    def clean_value(text: str) -> str:
        """Remove units and special characters from specification values."""
        if not text:
            return ""
        # Remove common units and symbols
        text = text.strip()
        text = text.replace("mm", "").replace("Ø", "").replace("°", "")
        text = text.replace("\t", "").replace("\n", "")
        return text.strip()
    
    # Strategy 1: Look for specification table (most common in product pages)
    # Typical structure: <table> with <tr><td>Label</td><td>Value</td></tr>
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label = cells[0].get_text().strip().lower()
                value = clean_value(cells[1].get_text())
                
                # Map common label variations to our field names
                # Check PCD/bolt circle FIRST before checking for "diameter" alone
                if 'pcd' in label or 'bolt circle' in label or 'pitch circle' in label:
                    raw['bolt_circle_mm'] = value
                elif 'center bore' in label or 'centre bore' in label or 'hub bore' in label:
                    raw['center_bore_mm'] = value
                elif 'outer diameter' in label or (('diameter' in label or 'rotor diameter' in label) and 'bolt' not in label and 'pcd' not in label):
                    raw['outer_diameter_mm'] = value
                elif 'thickness' in label and 'nominal' in label:
                    raw['nominal_thickness_mm'] = value
                elif 'thickness' in label and 'hat' not in label and 'overall' not in label and 'rotor' not in label:
                    raw['nominal_thickness_mm'] = value
                elif 'hat height' in label or 'hat-height' in label:
                    raw['hat_height_mm'] = value
                elif 'overall height' in label or 'overall-height' in label or 'total height' in label:
                    raw['overall_height_mm'] = value
                elif 'bolt hole' in label or 'hole count' in label or 'stud holes' in label:
                    raw['bolt_hole_count'] = value
                elif 'ventilation' in label or 'vented' in label:
                    raw['ventilation_type'] = value.lower()
                elif 'directional' in label:
                    raw['directionality'] = value.lower()
                elif 'weight' in label:
                    raw['rotor_weight_kg'] = value
                elif 'mounting' in label:
                    raw['mounting_type'] = value.lower()
                elif 'offset' in label:
                    raw['offset_mm'] = value
                elif 'part' in label or 'ref' in label or 'sku' in label or 'code' in label:
                    raw['ref'] = value
    
    # Strategy 2: Look for definition lists (dl/dt/dd)
    dls = soup.find_all('dl')
    for dl in dls:
        terms = dl.find_all('dt')
        definitions = dl.find_all('dd')
        for dt, dd in zip(terms, definitions):
            label = dt.get_text().strip().lower()
            value = clean_value(dd.get_text())
            
            # Check PCD first
            if 'pcd' in label or 'bolt circle' in label:
                raw['bolt_circle_mm'] = value
            elif 'diameter' in label and 'bolt' not in label:
                raw['outer_diameter_mm'] = value
            elif 'thickness' in label:
                raw['nominal_thickness_mm'] = value
            elif 'hat height' in label:
                raw['hat_height_mm'] = value
            elif 'overall height' in label:
                raw['overall_height_mm'] = value
            elif 'center bore' in label or 'centre bore' in label:
                raw['center_bore_mm'] = value
            elif 'bolt hole' in label:
                raw['bolt_hole_count'] = value
            elif 'part' in label or 'ref' in label:
                raw['ref'] = value
    
    # Strategy 3: Look for divs/spans with data attributes
    spec_divs = soup.find_all(['div', 'span'], class_=lambda x: x and ('spec' in x.lower() or 'product' in x.lower()))
    for div in spec_divs:
        # Check for data attributes
        if div.has_attr('data-diameter'):
            raw['outer_diameter_mm'] = clean_value(div.get('data-diameter'))
        if div.has_attr('data-thickness'):
            raw['nominal_thickness_mm'] = clean_value(div.get('data-thickness'))
        if div.has_attr('data-hat-height'):
            raw['hat_height_mm'] = clean_value(div.get('data-hat-height'))
    
    # Extract product reference from title, h1, or product code
    if 'ref' not in raw:
        # Try h1 title
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
            # Look for DBA part numbers (usually format: DBA####X or DBA#####XY)
            # Find all matches and take the longest one (most specific)
            matches = re.findall(r'DBA\s*\d+[A-Z0-9]*', title, re.IGNORECASE)
            if matches:
                # Take the longest match (most specific product code)
                longest_match = max(matches, key=lambda x: len(x.replace(' ', '')))
                raw['ref'] = longest_match.replace(' ', '')
        
        # Try product code meta or div
        product_code = soup.find(['div', 'span'], class_=lambda x: x and 'product-code' in x.lower())
        if product_code:
            raw['ref'] = clean_value(product_code.get_text())
    
    # Set defaults for fields that might not be in HTML
    if 'ventilation_type' not in raw:
        # Try to infer from product title or description
        title_text = soup.find('h1')
        if title_text:
            title_lower = title_text.get_text().lower()
            if 'slotted' in title_lower and 'drilled' in title_lower:
                raw['ventilation_type'] = 'drilled_slotted'
            elif 'slotted' in title_lower:
                raw['ventilation_type'] = 'slotted'
            elif 'drilled' in title_lower:
                raw['ventilation_type'] = 'drilled'
            elif 'vented' in title_lower:
                raw['ventilation_type'] = 'vented'
            else:
                raw['ventilation_type'] = 'vented'  # Default assumption
    
    if 'directionality' not in raw:
        raw['directionality'] = 'non_directional'  # Common default for DBA
    
    # Normalize and return
    return normalize_rotor(raw, source="dba")

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

def parse_ebc_pad_page(html: str) -> dict:
    """
    Parse an EBC pad product page and extract pad specifications.
    
    Args:
        html: HTML content of an EBC pad product page
    
    Returns:
        Normalized pad dict conforming to schema_pad.json
    """
    soup = BeautifulSoup(html, "html.parser")
    raw = {}
    
    def clean_value(text: str) -> str:
        """Remove units and special characters from specification values."""
        if not text:
            return ""
        text = text.strip()
        text = text.replace("mm", "").replace("²", "").replace("mm²", "")
        text = text.replace("\t", "").replace("\n", "")
        return text.strip()
    
    # Strategy 1: Look for specification table
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label = cells[0].get_text().strip().lower()
                value = clean_value(cells[1].get_text())
                
                # Map labels to field names
                if 'shape' in label and 'id' in label:
                    raw['shape_id'] = value
                elif 'shape' in label or 'shape code' in label:
                    raw['shape_id'] = value
                elif 'length' in label:
                    raw['length_mm'] = value
                elif 'height' in label:
                    raw['height_mm'] = value
                elif 'thickness' in label:
                    raw['thickness_mm'] = value
                elif 'swept area' in label or 'area' in label:
                    raw['swept_area_mm2'] = value
                elif 'backing' in label or 'plate type' in label:
                    raw['backing_plate_type'] = value
                elif 'part' in label or 'ref' in label or 'sku' in label or 'code' in label:
                    if 'shape' not in label:  # Don't confuse with shape_id
                        raw['catalog_ref'] = value
    
    # Strategy 2: Look for definition lists
    dls = soup.find_all('dl')
    for dl in dls:
        terms = dl.find_all('dt')
        definitions = dl.find_all('dd')
        for dt, dd in zip(terms, definitions):
            label = dt.get_text().strip().lower()
            value = clean_value(dd.get_text())
            
            if 'shape' in label:
                raw['shape_id'] = value
            elif 'length' in label:
                raw['length_mm'] = value
            elif 'height' in label:
                raw['height_mm'] = value
            elif 'thickness' in label:
                raw['thickness_mm'] = value
            elif 'swept area' in label:
                raw['swept_area_mm2'] = value
            elif 'backing' in label:
                raw['backing_plate_type'] = value
            elif 'part' in label or 'ref' in label:
                raw['catalog_ref'] = value
    
    # Strategy 3: Look for data attributes
    spec_divs = soup.find_all(['div', 'span'], class_=lambda x: x and ('spec' in x.lower() or 'pad' in x.lower()))
    for div in spec_divs:
        if div.has_attr('data-shape'):
            raw['shape_id'] = clean_value(div.get('data-shape'))
        if div.has_attr('data-length'):
            raw['length_mm'] = clean_value(div.get('data-length'))
        if div.has_attr('data-height'):
            raw['height_mm'] = clean_value(div.get('data-height'))
        if div.has_attr('data-thickness'):
            raw['thickness_mm'] = clean_value(div.get('data-thickness'))
    
    # Extract catalog ref from title/h1 if not found
    if 'catalog_ref' not in raw:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
            # Look for EBC part numbers (usually format: DP####XX or FA####XX)
            match = re.search(r'(DP|FA|EBC)\s*\d+[A-Z]*', title, re.IGNORECASE)
            if match:
                raw['catalog_ref'] = match.group(0).replace(' ', '')
        
        # Try product code div/span
        product_code = soup.find(['div', 'span'], class_=lambda x: x and 'product-code' in x.lower())
        if product_code:
            raw['catalog_ref'] = clean_value(product_code.get_text())
    
    # Extract shape_id from title if not found
    if 'shape_id' not in raw:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
            # Look for shape codes (often alphanumeric like "FA123" or just numbers)
            match = re.search(r'Shape\s*:?\s*([A-Z0-9]+)', title, re.IGNORECASE)
            if match:
                raw['shape_id'] = match.group(1)
    
    # Normalize and return
    return normalize_pad(raw, source="ebc")

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
    """
    Normalize raw pad data to conform to schema_pad.json.
    
    Args:
        raw: Dict with raw string/numeric values from scraper
        source: Brand/source identifier (e.g., 'ebc', 'ferodo')
    
    Returns:
        Dict conforming to PadSpec schema
    """
    def safe_float(val):
        """Convert to float, return None if not possible."""
        if val is None or val == "":
            return None
        try:
            # Clean common units
            if isinstance(val, str):
                val = val.replace("mm", "").replace("²", "").strip()
            return float(val)
        except (ValueError, TypeError):
            return None
    
    # Required fields - convert to proper types
    shape_id = raw.get("shape_id") or raw.get("shape") or ""
    length_mm = safe_float(raw.get("length_mm") or raw.get("length"))
    height_mm = safe_float(raw.get("height_mm") or raw.get("height"))
    thickness_mm = safe_float(raw.get("thickness_mm") or raw.get("thickness"))
    
    # Optional fields
    swept_area_mm2 = safe_float(raw.get("swept_area_mm2") or raw.get("swept_area"))
    backing_plate_type = raw.get("backing_plate_type") or raw.get("backing_plate") or None
    
    # Brand and catalog ref
    brand = source.lower()
    catalog_ref = raw.get("catalog_ref") or raw.get("ref") or raw.get("part_number") or ""
    
    return {
        "shape_id": shape_id,
        "length_mm": length_mm,
        "height_mm": height_mm,
        "thickness_mm": thickness_mm,
        "swept_area_mm2": swept_area_mm2,
        "backing_plate_type": backing_plate_type,
        "brand": brand,
        "catalog_ref": catalog_ref
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
