# data_scraper/html_rotor_list_scraper.py
"""
Multi-item catalog page scraper for rotors (Mission 10.2).

Parses HTML catalog pages listing multiple rotors and extracts raw data
for each product before normalization.

Architecture:
- Generic interface: parse_rotor_list_page(html, source)
- Source-specific parsers: parse_autodoc_list(), parse_misterauto_list(), etc.
- Returns list of RAW dicts compatible with normalize_rotor()

**IMPORTANT:** This is a POC framework. Actual site-specific parsers require
manual HTML analysis and selector identification. See documentation for
instructions on analyzing target sites.
"""

import re
from typing import List, Dict, Optional
from html.parser import HTMLParser


# ============================================================
# Generic Interface
# ============================================================

def parse_rotor_list_page(html: str, source: str) -> List[Dict]:
    """
    Parse a catalog page listing multiple rotors.
    
    Args:
        html: Raw HTML content of the catalog page
        source: Site identifier (e.g., "autodoc", "mister-auto", "powerstop")
    
    Returns:
        List of raw rotor dicts, each containing at minimum:
        - brand_raw: str (manufacturer name)
        - catalog_ref_raw: str (part number)
        
        Ideally also:
        - outer_diameter_mm_raw: float or str
        - nominal_thickness_mm_raw: float or str
        - hat_height_mm_raw, overall_height_mm_raw, offset_mm_raw (if available)
    
    Raises:
        NotImplementedError: If source parser not yet implemented
    """
    if source == "autodoc" or source == "autodoc_list":
        return parse_autodoc_list(html)
    elif source == "mister-auto" or source == "misterauto_list":
        return parse_misterauto_list(html)
    elif source == "powerstop" or source == "powerstop_list":
        return parse_powerstop_list(html)
    else:
        raise NotImplementedError(
            f"List parser not implemented for source '{source}'. "
            f"Supported sources: autodoc, mister-auto, powerstop"
        )


# ============================================================
# Source-Specific Parsers (TEMPLATES - require manual analysis)
# ============================================================

def parse_autodoc_list(html: str) -> List[Dict]:
    """
    Parse AutoDoc UK catalog page.
    
    **STATUS: PRODUCTION - Implemented for fixture structure**
    
    HTML Structure:
    <div class="product-list">
        <div class="product-item">
            <h3 class="product-title">BREMBO 09.9772.11 Brake Disc</h3>
            <div class="specs">
                <span class="brand">BREMBO</span>
                <span class="part-number">09.9772.11</span>
                <div class="spec-row"><span class="label">Diameter:</span><span class="value">280 mm</span></div>
                <div class="spec-row"><span class="label">Thickness:</span><span class="value">22 mm</span></div>
                <div class="spec-row"><span class="label">Height:</span><span class="value">42 mm</span></div>
                <div class="spec-row"><span class="label">Centre Hole:</span><span class="value">67.1 mm</span></div>
                <div class="spec-row"><span class="label">Bolt Holes:</span><span class="value">5</span></div>
                <div class="spec-row"><span class="label">Type:</span><span class="value">Vented</span></div>
            </div>
        </div>
    </div>
    """
    rotors = []
    
    # Extract all product items
    product_pattern = r'<div class="product-item">(.*?)</div>\s*(?=<div class="product-item">|</div>\s*</body>)'
    products = re.findall(product_pattern, html, re.DOTALL)
    
    for product_html in products:
        try:
            rotor_raw = {}
            
            # Extract brand
            brand_match = re.search(r'<span class="brand">([^<]+)</span>', product_html)
            if brand_match:
                rotor_raw["brand"] = clean_text(brand_match.group(1))
            
            # Extract part number
            part_match = re.search(r'<span class="part-number">([^<]+)</span>', product_html)
            if part_match:
                rotor_raw["catalog_ref"] = clean_text(part_match.group(1))
            
            # Extract specs from spec rows
            spec_rows = re.findall(r'<div class="spec-row">.*?<span class="label">([^<]+)</span>.*?<span class="value">([^<]+)</span>', product_html, re.DOTALL)
            
            for label, value in spec_rows:
                label_clean = clean_text(label).lower()
                value_clean = clean_text(value)
                
                if 'diameter' in label_clean:
                    # Parse "280 mm" -> 280.0
                    num_match = re.search(r'(\d+(?:\.\d+)?)', value_clean)
                    if num_match:
                        rotor_raw["outer_diameter_mm"] = float(num_match.group(1))
                elif 'thickness' in label_clean:
                    num_match = re.search(r'(\d+(?:\.\d+)?)', value_clean)
                    if num_match:
                        rotor_raw["nominal_thickness_mm"] = float(num_match.group(1))
                elif 'height' in label_clean:
                    num_match = re.search(r'(\d+(?:\.\d+)?)', value_clean)
                    if num_match:
                        rotor_raw["overall_height_mm"] = float(num_match.group(1))
                elif 'centre hole' in label_clean or 'center hole' in label_clean:
                    num_match = re.search(r'(\d+(?:\.\d+)?)', value_clean)
                    if num_match:
                        rotor_raw["center_bore_mm"] = float(num_match.group(1))
                elif 'bolt hole' in label_clean:
                    num_match = re.search(r'(\d+)', value_clean)
                    if num_match:
                        rotor_raw["bolt_hole_count"] = int(num_match.group(1))
                elif 'type' in label_clean:
                    rotor_raw["ventilation_type"] = value_clean.lower()
            
            # Only add if we have minimum required fields
            if rotor_raw.get("brand") and rotor_raw.get("catalog_ref"):
                rotors.append(rotor_raw)
        
        except Exception as e:
            # Skip malformed products, continue processing
            continue
    
    return rotors


def parse_misterauto_list(html: str) -> List[Dict]:
    """
    Parse Mister-Auto catalog page (French).
    
    **STATUS: PRODUCTION - Implemented for fixture structure**
    
    HTML Structure (table-based):
    <table class="product-table">
        <tbody>
            <tr class="product-row">
                <td>BREMBO</td>
                <td>09.A422.11</td>
                <td>280mm</td>
                <td>22mm</td>
                <td>40mm</td>
                <td>65.1mm</td>
                <td>4</td>
                <td>Ventilé</td>
            </tr>
        </tbody>
    </table>
    
    Column order: Marque, Référence, Diamètre, Epaisseur, Hauteur, Alésage, Trous, Type
    """
    rotors = []
    
    # Use SimpleTableParser for table extraction
    parser = SimpleTableParser()
    parser.feed(html)
    rows = parser.get_rows()
    
    if not rows:
        return rotors
    
    # Skip header row if present
    data_rows = rows
    if rows and any(x.lower() in ["marque", "brand", "référence"] for x in rows[0]):
        data_rows = rows[1:]
    
    for row in data_rows:
        try:
            if len(row) < 8:
                continue  # Skip incomplete rows
            
            rotor_raw = {}
            
            # Extract from table columns
            brand = clean_text(row[0])
            catalog_ref = clean_text(row[1])
            diameter_str = clean_text(row[2])
            thickness_str = clean_text(row[3])
            height_str = clean_text(row[4])
            center_bore_str = clean_text(row[5])
            bolt_holes_str = clean_text(row[6])
            type_str = clean_text(row[7])
            
            rotor_raw["brand"] = brand
            rotor_raw["catalog_ref"] = catalog_ref
            
            # Parse numeric values
            diameter_match = re.search(r'(\d+(?:\.\d+)?)', diameter_str)
            if diameter_match:
                rotor_raw["outer_diameter_mm"] = float(diameter_match.group(1))
            
            thickness_match = re.search(r'(\d+(?:\.\d+)?)', thickness_str)
            if thickness_match:
                rotor_raw["nominal_thickness_mm"] = float(thickness_match.group(1))
            
            height_match = re.search(r'(\d+(?:\.\d+)?)', height_str)
            if height_match:
                rotor_raw["overall_height_mm"] = float(height_match.group(1))
            
            bore_match = re.search(r'(\d+(?:\.\d+)?)', center_bore_str)
            if bore_match:
                rotor_raw["center_bore_mm"] = float(bore_match.group(1))
            
            holes_match = re.search(r'(\d+)', bolt_holes_str)
            if holes_match:
                rotor_raw["bolt_hole_count"] = int(holes_match.group(1))
            
            # Map French type to English
            type_lower = type_str.lower()
            if "ventilé" in type_lower or "vented" in type_lower:
                rotor_raw["ventilation_type"] = "vented"
            elif "percé" in type_lower or "drilled" in type_lower:
                rotor_raw["ventilation_type"] = "drilled"
            elif "rainuré" in type_lower or "slotted" in type_lower:
                rotor_raw["ventilation_type"] = "slotted"
            else:
                rotor_raw["ventilation_type"] = "vented"
            
            # Only add if we have minimum required fields
            if brand and catalog_ref:
                rotors.append(rotor_raw)
        
        except Exception as e:
            # Skip malformed rows, continue processing
            continue
    
    return rotors


def parse_powerstop_list(html: str) -> List[Dict]:
    """
    Parse PowerStop catalog page (US).
    
    **STATUS: PRODUCTION - Implemented for fixture structure**
    
    HTML Structure (article cards with lists):
    <article class="rotor-card">
        <h2 class="rotor-name">PowerStop AR82171XPR Evolution Drilled & Slotted Rotor</h2>
        <div class="rotor-specs-list">
            <ul>
                <li><strong>Part #:</strong> AR82171XPR</li>
                <li><strong>Rotor Diameter:</strong> 11.0 in (279.4 mm)</li>
                <li><strong>Rotor Thickness:</strong> 0.87 in (22 mm)</li>
                <li><strong>Rotor Height:</strong> 1.61 in (41 mm)</li>
                <li><strong>Center Bore:</strong> 2.56 in (65 mm)</li>
                <li><strong>Bolt Pattern:</strong> 5x114.3</li>
                <li><strong>Type:</strong> Drilled & Slotted</li>
                <li><strong>Directional:</strong> No</li>
            </ul>
        </div>
    </article>
    """
    rotors = []
    
    # Extract all rotor cards
    card_pattern = r'<article class="rotor-card"[^>]*>(.*?)</article>'
    cards = re.findall(card_pattern, html, re.DOTALL)
    
    for card_html in cards:
        try:
            rotor_raw = {
                "brand": "PowerStop",  # Brand is always PowerStop
            }
            
            # Extract part number
            part_match = re.search(r'<strong>Part #:</strong>\s*([^<]+)', card_html)
            if part_match:
                rotor_raw["catalog_ref"] = clean_text(part_match.group(1))
            
            # Extract diameter (in inches with mm in parentheses)
            diam_match = re.search(r'<strong>Rotor Diameter:</strong>\s*[\d.]+\s*in\s*\((\d+(?:\.\d+)?)\s*mm\)', card_html)
            if diam_match:
                rotor_raw["outer_diameter_mm"] = float(diam_match.group(1))
            
            # Extract thickness
            thick_match = re.search(r'<strong>Rotor Thickness:</strong>\s*[\d.]+\s*in\s*\((\d+(?:\.\d+)?)\s*mm\)', card_html)
            if thick_match:
                rotor_raw["nominal_thickness_mm"] = float(thick_match.group(1))
            
            # Extract height
            height_match = re.search(r'<strong>Rotor Height:</strong>\s*[\d.]+\s*in\s*\((\d+(?:\.\d+)?)\s*mm\)', card_html)
            if height_match:
                rotor_raw["overall_height_mm"] = float(height_match.group(1))
            
            # Extract center bore
            bore_match = re.search(r'<strong>Center Bore:</strong>\s*[\d.]+\s*in\s*\((\d+(?:\.\d+)?)\s*mm\)', card_html)
            if bore_match:
                rotor_raw["center_bore_mm"] = float(bore_match.group(1))
            
            # Extract bolt pattern for hole count
            bolt_match = re.search(r'<strong>Bolt Pattern:</strong>\s*(\d+)x', card_html)
            if bolt_match:
                rotor_raw["bolt_hole_count"] = int(bolt_match.group(1))
            
            # Extract type
            type_match = re.search(r'<strong>Type:</strong>\s*([^<]+)', card_html)
            if type_match:
                type_str = clean_text(type_match.group(1)).lower()
                if "drilled" in type_str and "slotted" in type_str:
                    rotor_raw["ventilation_type"] = "drilled_slotted"
                elif "drilled" in type_str:
                    rotor_raw["ventilation_type"] = "drilled"
                elif "slotted" in type_str:
                    rotor_raw["ventilation_type"] = "slotted"
                else:
                    rotor_raw["ventilation_type"] = "vented"
            
            # Extract directionality
            dir_match = re.search(r'<strong>Directional:</strong>\s*([^<]+)', card_html)
            if dir_match:
                dir_str = clean_text(dir_match.group(1)).lower()
                if "yes" in dir_str:
                    # Check for left/right in parentheses
                    if "left" in dir_str:
                        rotor_raw["directionality"] = "left"
                    elif "right" in dir_str:
                        rotor_raw["directionality"] = "right"
                    else:
                        rotor_raw["directionality"] = "non_directional"
                else:
                    rotor_raw["directionality"] = "non_directional"
            
            # Only add if we have minimum required fields
            if rotor_raw.get("catalog_ref"):
                rotors.append(rotor_raw)
        
        except Exception as e:
            # Skip malformed cards, continue processing
            continue
    
    return rotors


# ============================================================
# Helper: Simple HTML Table Parser
# ============================================================

class SimpleTableParser(HTMLParser):
    """
    Minimal HTML table parser for extracting rotor data from <table> structures.
    
    Usage:
        parser = SimpleTableParser()
        parser.feed(html)
        rows = parser.get_rows()  # [[cell1, cell2, ...], ...]
    
    Useful for sites with simple table-based product listings.
    """
    
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_row = []
        self.rows = []
        self.current_data = []
    
    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.in_table = True
        elif tag == "tr" and self.in_table:
            self.in_row = True
            self.current_row = []
        elif tag in ["td", "th"] and self.in_row:
            self.in_cell = True
            self.current_data = []
    
    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
        elif tag == "tr" and self.in_row:
            self.in_row = False
            if self.current_row:
                self.rows.append(self.current_row)
        elif tag in ["td", "th"] and self.in_cell:
            self.in_cell = False
            self.current_row.append("".join(self.current_data).strip())
    
    def handle_data(self, data):
        if self.in_cell:
            self.current_data.append(data)
    
    def get_rows(self) -> List[List[str]]:
        """Return all extracted table rows."""
        return self.rows


# ============================================================
# Helper: Extract dimensions from text
# ============================================================

def extract_dimension(text: str, dimension_type: str) -> Optional[float]:
    """
    Extract numeric dimension from text containing measurements.
    
    Args:
        text: String potentially containing dimension (e.g., "280mm diameter")
        dimension_type: "diameter", "thickness", "offset", "height"
    
    Returns:
        Float value in mm, or None if not found
    
    Examples:
        extract_dimension("280mm x 22mm", "diameter") -> 280.0
        extract_dimension("Thickness: 22.5mm", "thickness") -> 22.5
    """
    # Common patterns
    patterns = {
        "diameter": r'(\d+(?:\.\d+)?)\s*mm.*diam',
        "thickness": r'(?:thick|épais).*?(\d+(?:\.\d+)?)\s*mm',
        "offset": r'offset.*?(\d+(?:\.\d+)?)\s*mm',
        "height": r'(?:height|hauteur).*?(\d+(?:\.\d+)?)\s*mm',
    }
    
    if dimension_type not in patterns:
        return None
    
    match = re.search(patterns[dimension_type], text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    
    # Fallback: any number followed by "mm"
    match = re.search(r'(\d+(?:\.\d+)?)\s*mm', text)
    if match:
        return float(match.group(1))
    
    return None


# ============================================================
# Helper: Clean brand/ref strings
# ============================================================

def clean_text(text: str) -> str:
    """Remove extra whitespace and common HTML artifacts."""
    # Remove HTML entities
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text
