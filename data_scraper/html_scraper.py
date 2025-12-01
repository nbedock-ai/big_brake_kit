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

def parse_wheelsize_vehicle_page(html: str) -> dict:
    """
    Parse a Wheel-Size vehicle page and extract vehicle/hub/wheel specifications.
    
    Args:
        html: HTML content of a Wheel-Size vehicle page
    
    Returns:
        Raw dict with vehicle specs (not yet normalized - use normalize_vehicle in Mission 6)
    """
    soup = BeautifulSoup(html, "html.parser")
    raw = {}
    
    def clean_value(text: str) -> str:
        """Remove common formatting from specification values."""
        if not text:
            return ""
        text = text.strip()
        text = text.replace("\t", "").replace("\n", " ")
        # Keep units for now - normalization happens in Mission 6
        return text.strip()
    
    # Strategy 1: Look for specification tables
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label = cells[0].get_text().strip().lower()
                value = clean_value(cells[1].get_text())
                
                # Vehicle identification
                if 'make' in label or 'manufacturer' in label:
                    raw['make'] = value
                elif 'model' in label:
                    raw['model'] = value
                elif 'generation' in label:
                    raw['generation'] = value
                elif 'year from' in label or 'start year' in label:
                    raw['year_from_raw'] = value
                elif 'year to' in label or 'end year' in label:
                    raw['year_to_raw'] = value
                elif ('year' in label or 'years' in label) and 'from' not in label and 'to' not in label:
                    # Handle "Years: 2016-2020" format
                    raw['years_raw'] = value
                
                # Hub specifications
                elif 'pcd' in label or 'bolt pattern' in label or 'bolt circle' in label:
                    raw['hub_bolt_pattern_raw'] = value
                elif 'bolt holes' in label or 'stud count' in label or 'lugs' in label:
                    raw['hub_bolt_hole_count_raw'] = value
                elif 'center bore' in label or 'centre bore' in label or 'hub bore' in label:
                    raw['hub_center_bore_mm_raw'] = value
                
                # Front wheel/tire specs
                elif 'front wheel width' in label or 'front rim width' in label:
                    raw['front_wheel_width_in_raw'] = value
                elif 'front wheel diameter' in label or 'front rim diameter' in label or 'front wheel size' in label:
                    raw['front_wheel_diameter_in_raw'] = value
                elif 'front tire' in label:
                    raw['front_tire_dimensions_raw'] = value
                
                # Rear wheel/tire specs
                elif 'rear wheel width' in label or 'rear rim width' in label:
                    raw['rear_wheel_width_in_raw'] = value
                elif 'rear wheel diameter' in label or 'rear rim diameter' in label or 'rear wheel size' in label:
                    raw['rear_wheel_diameter_in_raw'] = value
                elif 'rear tire' in label:
                    raw['rear_tire_dimensions_raw'] = value
                
                # Rotor specifications
                elif 'front rotor diameter' in label or 'front disc diameter' in label:
                    raw['front_rotor_outer_diameter_mm_raw'] = value
                elif 'front rotor thickness' in label or 'front disc thickness' in label:
                    raw['front_rotor_thickness_mm_raw'] = value
                elif 'rear rotor diameter' in label or 'rear disc diameter' in label:
                    raw['rear_rotor_outer_diameter_mm_raw'] = value
                elif 'rear rotor thickness' in label or 'rear disc thickness' in label:
                    raw['rear_rotor_thickness_mm_raw'] = value
    
    # Strategy 2: Look for definition lists
    dls = soup.find_all('dl')
    for dl in dls:
        terms = dl.find_all('dt')
        definitions = dl.find_all('dd')
        for dt, dd in zip(terms, definitions):
            label = dt.get_text().strip().lower()
            value = clean_value(dd.get_text())
            
            if 'make' in label:
                raw['make'] = value
            elif 'model' in label:
                raw['model'] = value
            elif 'generation' in label:
                raw['generation'] = value
            elif 'pcd' in label or 'bolt pattern' in label:
                raw['hub_bolt_pattern_raw'] = value
            elif 'center bore' in label or 'centre bore' in label:
                raw['hub_center_bore_mm_raw'] = value
    
    # Strategy 3: Look for data attributes
    spec_divs = soup.find_all(['div', 'span'], attrs=lambda x: x and any(k.startswith('data-') for k in x.keys()) if x else False)
    for div in spec_divs:
        if div.has_attr('data-make'):
            raw['make'] = clean_value(div.get('data-make'))
        if div.has_attr('data-model'):
            raw['model'] = clean_value(div.get('data-model'))
        if div.has_attr('data-pcd'):
            raw['hub_bolt_pattern_raw'] = clean_value(div.get('data-pcd'))
        if div.has_attr('data-bore'):
            raw['hub_center_bore_mm_raw'] = clean_value(div.get('data-bore'))
    
    # Extract make/model from title/h1 if not found
    if 'make' not in raw or 'model' not in raw:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
            # Try to parse "Honda Civic 2016-2020" or similar formats
            parts = title.split()
            if len(parts) >= 2 and 'make' not in raw:
                raw['make'] = parts[0]
            if len(parts) >= 2 and 'model' not in raw:
                raw['model'] = parts[1]
    
    # Parse bolt pattern "5x114.3" into components if present
    if 'hub_bolt_pattern_raw' in raw and 'x' in raw['hub_bolt_pattern_raw']:
        pattern = raw['hub_bolt_pattern_raw']
        parts = pattern.split('x')
        if len(parts) == 2:
            raw['hub_bolt_hole_count_raw'] = parts[0].strip()
            raw['hub_bolt_circle_mm_raw'] = parts[1].strip()
    
    return raw

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
    """
    Normalize raw vehicle data to conform to schema_vehicle.json.
    
    Args:
        raw: Dict with raw string values from parse_wheelsize_vehicle_page
        source: Source identifier (e.g., 'wheelsize')
    
    Returns:
        Dict conforming to VehicleBrakeFitment schema
    """
    import re
    
    if source.lower() != "wheelsize":
        raise NotImplementedError(f"normalize_vehicle: unsupported source '{source}'")
    
    def parse_float_mm(val):
        """Parse float from string with mm unit."""
        if val is None or val == "":
            return None
        try:
            # Clean: strip, remove "mm", replace comma
            cleaned = str(val).strip().replace("mm", "").replace("MM", "").replace(",", ".").strip()
            return float(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None
    
    def parse_int_safe(val):
        """Parse int from string."""
        if val is None or val == "":
            return None
        try:
            return int(str(val).strip())
        except (ValueError, TypeError):
            return None
    
    # 1. Vehicle identification (required)
    make = raw.get("make", "").strip()
    model = raw.get("model", "").strip()
    if not make or not model:
        raise ValueError("normalize_vehicle: 'make' and 'model' are required")
    
    generation = raw.get("generation", "").strip() or None
    
    # 2. Years (year_from required, year_to optional)
    year_from = None
    year_to = None
    
    # Try explicit year_from_raw
    if raw.get("year_from_raw"):
        year_from = parse_int_safe(raw["year_from_raw"])
    
    # Try explicit year_to_raw
    if raw.get("year_to_raw"):
        year_to = parse_int_safe(raw["year_to_raw"])
    
    # If not found, parse years_raw "2016-2020" or "2016-"
    if year_from is None and raw.get("years_raw"):
        years_match = re.match(r"(\d{4})\s*-\s*(\d{4})?", raw["years_raw"])
        if years_match:
            year_from = int(years_match.group(1))
            if years_match.group(2):
                year_to = int(years_match.group(2))
    
    if year_from is None:
        raise ValueError("normalize_vehicle: 'year_from' is required but could not be parsed")
    
    # 3. Hub specifications (all required)
    hub_bolt_hole_count = None
    hub_bolt_circle_mm = None
    
    # Try explicit values first
    if raw.get("hub_bolt_hole_count_raw"):
        hub_bolt_hole_count = parse_int_safe(raw["hub_bolt_hole_count_raw"])
    
    if raw.get("hub_bolt_circle_mm_raw"):
        hub_bolt_circle_mm = parse_float_mm(raw["hub_bolt_circle_mm_raw"])
    
    # If not found, parse from hub_bolt_pattern_raw "5x114.3"
    if (hub_bolt_hole_count is None or hub_bolt_circle_mm is None) and raw.get("hub_bolt_pattern_raw"):
        pattern_match = re.match(r"(\d+)\s*[xX]\s*([\d.]+)", raw["hub_bolt_pattern_raw"])
        if pattern_match:
            if hub_bolt_hole_count is None:
                hub_bolt_hole_count = int(pattern_match.group(1))
            if hub_bolt_circle_mm is None:
                hub_bolt_circle_mm = float(pattern_match.group(2))
    
    if hub_bolt_hole_count is None or hub_bolt_circle_mm is None:
        raise ValueError("normalize_vehicle: 'hub_bolt_hole_count' and 'hub_bolt_circle_mm' are required")
    
    # Center bore (required)
    hub_center_bore_mm = parse_float_mm(raw.get("hub_center_bore_mm_raw"))
    if hub_center_bore_mm is None:
        raise ValueError("normalize_vehicle: 'hub_center_bore_mm' is required")
    
    # 4. Rotor OEM aggregation (optional)
    rotor_diameters = []
    rotor_thicknesses = []
    
    if raw.get("front_rotor_outer_diameter_mm_raw"):
        d = parse_float_mm(raw["front_rotor_outer_diameter_mm_raw"])
        if d:
            rotor_diameters.append(d)
    
    if raw.get("rear_rotor_outer_diameter_mm_raw"):
        d = parse_float_mm(raw["rear_rotor_outer_diameter_mm_raw"])
        if d:
            rotor_diameters.append(d)
    
    if raw.get("front_rotor_thickness_mm_raw"):
        t = parse_float_mm(raw["front_rotor_thickness_mm_raw"])
        if t:
            rotor_thicknesses.append(t)
    
    if raw.get("rear_rotor_thickness_mm_raw"):
        t = parse_float_mm(raw["rear_rotor_thickness_mm_raw"])
        if t:
            rotor_thicknesses.append(t)
    
    max_rotor_diameter_mm = max(rotor_diameters) if rotor_diameters else None
    rotor_thickness_min_mm = min(rotor_thicknesses) if rotor_thicknesses else None
    rotor_thickness_max_mm = max(rotor_thicknesses) if rotor_thicknesses else None
    
    # 5. Fields not provided by Wheel-Size (set to None)
    knuckle_bolt_spacing_mm = None
    knuckle_bolt_orientation_deg = None
    wheel_inner_barrel_clearance_mm = None
    
    # 6. Build final dict conforming to schema
    return {
        "make": make,
        "model": model,
        "generation": generation,
        "year_from": year_from,
        "year_to": year_to,
        "hub_bolt_circle_mm": hub_bolt_circle_mm,
        "hub_bolt_hole_count": hub_bolt_hole_count,
        "hub_center_bore_mm": hub_center_bore_mm,
        "knuckle_bolt_spacing_mm": knuckle_bolt_spacing_mm,
        "knuckle_bolt_orientation_deg": knuckle_bolt_orientation_deg,
        "max_rotor_diameter_mm": max_rotor_diameter_mm,
        "wheel_inner_barrel_clearance_mm": wheel_inner_barrel_clearance_mm,
        "rotor_thickness_min_mm": rotor_thickness_min_mm,
        "rotor_thickness_max_mm": rotor_thickness_max_mm
    }
