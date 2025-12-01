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
    
    **STATUS: TEMPLATE - Requires manual HTML structure analysis**
    
    TODO: Manually analyze https://www.autodoc.co.uk/car-parts/brake-disc-10132
    1. View page source (Ctrl+U)
    2. Identify product list container (table, ul, div.product-list, etc.)
    3. Identify individual product blocks/rows
    4. Extract selectors for: brand, part number, diameter, thickness
    5. Implement extraction logic below
    
    Expected structure pattern (example - verify with real HTML):
    <div class="product-list">
        <div class="product-item">
            <span class="brand">Bosch</span>
            <span class="part-num">0986479XXX</span>
            <span class="diameter">280mm</span>
            <span class="thickness">22mm</span>
        </div>
        ...
    </div>
    """
    rotors = []
    
    # TEMPLATE: Regex pattern approach (simple but fragile)
    # Replace with actual selectors after HTML analysis
    pattern = r'<div class="product-item">.*?brand">(.*?)</.*?part-num">(.*?)</.*?</div>'
    matches = re.findall(pattern, html, re.DOTALL)
    
    for match in matches:
        # Example extraction - adapt based on real HTML
        rotor_raw = {
            "brand_raw": "AutoDoc",  # Replace with extracted value
            "catalog_ref_raw": "PLACEHOLDER",  # Replace with extracted value
            "source": "autodoc"
        }
        rotors.append(rotor_raw)
    
    # Return empty list if no products found (avoid crashes)
    return rotors


def parse_misterauto_list(html: str) -> List[Dict]:
    """
    Parse Mister-Auto catalog page.
    
    **STATUS: TEMPLATE - Requires manual HTML structure analysis**
    
    TODO: Manually analyze https://www.mister-auto.com/brake-discs/
    Follow same steps as parse_autodoc_list()
    
    Common EU catalog patterns to look for:
    - Table rows: <table><tr><td>brand</td><td>ref</td>...</tr></table>
    - Product cards: <article class="product">...</article>
    - JSON-LD structured data: <script type="application/ld+json">
    """
    rotors = []
    
    # TEMPLATE: Implement after HTML analysis
    # Example placeholder
    if "mister-auto" in html.lower():
        pass  # Add extraction logic
    
    return rotors


def parse_powerstop_list(html: str) -> List[Dict]:
    """
    Parse PowerStop catalog page.
    
    **STATUS: TEMPLATE - Requires manual HTML structure analysis**
    
    TODO: Manually analyze https://www.powerstop.com/product-category/brake-rotors/
    
    PowerStop often uses WooCommerce (WordPress e-commerce):
    - Look for: <ul class="products">
    - Product items: <li class="product">
    - SKU in data attributes or meta fields
    """
    rotors = []
    
    # TEMPLATE: Implement after HTML analysis
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
