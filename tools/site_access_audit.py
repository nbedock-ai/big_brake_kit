"""
Site Access Audit Tool (Mission 10.5)

Audits all seed URLs to determine:
1. Which sites are accessible without headless browser
2. What level of bot protection they have
3. Which data fields are present in the HTML

Generates JSON and Markdown reports for planning future scraping missions.
"""

import csv
import json
import os
import re
import sys
import urllib.request
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse


# ============================================================
# Seed Collection
# ============================================================

def collect_seeds() -> List[Dict]:
    """
    Collect all seed URLs from CSV files in the project.
    
    Returns:
        List of dicts with keys: kind, source, url, page_type, notes
    """
    seeds = []
    
    # Map CSV file to kind
    seed_files = {
        "data_scraper/exporters/urls_seed_rotors.csv": "rotor",
        "data_scraper/exporters/urls_seed_pads.csv": "pad",
        "data_scraper/exporters/urls_seed_vehicles.csv": "vehicle",
    }
    
    for csv_path, kind in seed_files.items():
        if not os.path.exists(csv_path):
            print(f"[WARNING] Seed file not found: {csv_path}")
            continue
        
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                source = row.get("source", "").strip()
                url = row.get("url", "").strip()
                page_type = row.get("page_type", "product").strip().lower()
                notes = row.get("notes", "").strip()
                
                if source and url:
                    seeds.append({
                        "kind": kind,
                        "source": source,
                        "url": url,
                        "page_type": page_type,
                        "notes": notes,
                    })
    
    return seeds


# ============================================================
# URL Probing
# ============================================================

def probe_url(seed: Dict, save_html: bool = False) -> Dict:
    """
    Probe a single URL to check accessibility and bot protection.
    
    Args:
        seed: Dict with kind, source, url, etc.
        save_html: Whether to save HTML sample on success
    
    Returns:
        Dict with status_code, error, suspected_bot_protection, html_sample_path, etc.
    """
    url = seed["url"]
    parsed = urlparse(url)
    domain = parsed.netloc
    
    result = {
        "kind": seed["kind"],
        "source": seed["source"],
        "url": url,
        "domain": domain,
        "page_type": seed.get("page_type", "product"),
        "notes": seed.get("notes", ""),
        "status_code": None,
        "error": None,
        "suspected_bot_protection": False,
        "html_sample_path": None,
        "html_length": 0,
    }
    
    try:
        # Realistic User-Agent
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result["status_code"] = response.status
            html = response.read().decode('utf-8', errors='replace')
            result["html_length"] = len(html)
            
            # Check for bot protection signatures
            bot_signatures = [
                "cloudflare",
                "attention required",
                "enable javascript",
                "captcha",
                "access denied",
                "bot protection",
                "please verify you are a human",
            ]
            
            html_lower = html.lower()
            for sig in bot_signatures:
                if sig in html_lower:
                    result["suspected_bot_protection"] = True
                    break
            
            # Check for JS-only sites (very short HTML with minimal content)
            if len(html) < 5000 and "<noscript>" in html_lower:
                result["suspected_bot_protection"] = True
            
            # Save HTML sample if requested and no bot protection
            if save_html and not result["suspected_bot_protection"]:
                sample_dir = f"artifacts/site_html_samples/{seed['kind']}/{domain}"
                os.makedirs(sample_dir, exist_ok=True)
                
                filename = f"{seed['source']}_{seed['page_type']}.html"
                filepath = os.path.join(sample_dir, filename)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(html)
                
                result["html_sample_path"] = filepath
                result["_html_content"] = html  # For field analysis
    
    except HTTPError as e:
        result["status_code"] = e.code
        result["error"] = f"HTTP {e.code}: {e.reason}"
        
        # 403/503 typically indicates bot protection
        if e.code in [403, 503]:
            result["suspected_bot_protection"] = True
    
    except URLError as e:
        result["error"] = f"URL Error: {e.reason}"
    
    except Exception as e:
        result["error"] = f"Exception: {type(e).__name__}: {str(e)}"
    
    return result


# ============================================================
# HTML Field Detection
# ============================================================

def analyze_html_fields(kind: str, html: str) -> Dict[str, bool]:
    """
    Analyze HTML to detect which data fields are present.
    
    Args:
        kind: "rotor", "pad", "vehicle", etc.
        html: HTML content
    
    Returns:
        Dict with field names as keys and True/False as values
    """
    html_lower = html.lower()
    
    if kind == "rotor":
        return _detect_rotor_fields(html, html_lower)
    elif kind == "pad":
        return _detect_pad_fields(html, html_lower)
    elif kind == "vehicle":
        return _detect_vehicle_fields(html, html_lower)
    else:
        return {}


def _detect_rotor_fields(html: str, html_lower: str) -> Dict[str, bool]:
    """Detect rotor-specific fields in HTML."""
    fields = {}
    
    # Diameter (most common field)
    diameter_patterns = [
        r'\b\d{3}\s*mm\b',  # "280 mm", "300mm"
        r'diameter[:\s]*\d{2,3}',
        r'diamètre[:\s]*\d{2,3}',
        r'Ø\s*\d{2,3}',
    ]
    fields["diameter_mm"] = any(re.search(p, html_lower) for p in diameter_patterns)
    
    # Thickness
    thickness_patterns = [
        r'thickness[:\s]*\d{1,2}',
        r'paisseur[:\s]*\d{1,2}',  # French (with or without é)
        r'\b\d{1,2}\s*mm\s*(thick|pais)',
    ]
    fields["thickness_mm"] = any(re.search(p, html_lower) for p in thickness_patterns)
    
    # Height (overall/total)
    height_patterns = [
        r'height[:\s]*\d{1,2}',
        r'hauteur[:\s]*\d{1,2}',  # French
        r'overall[:\s]*height',
    ]
    fields["height_mm"] = any(re.search(p, html_lower) for p in height_patterns)
    
    # Center bore / hub bore
    bore_patterns = [
        r'(center|centre)\s*(bore|hole)',
        r'alésage',
        r'hub\s*bore',
        r'\b\d{2}\.\d\s*mm\s*bore',
    ]
    fields["center_bore_mm"] = any(re.search(p, html_lower) for p in bore_patterns)
    
    # Bolt holes / bolt pattern
    bolt_patterns = [
        r'bolt\s*(hole|pattern)',
        r'trous\s*de\s*fixation',
        r'\d\s*x\s*\d{2,3}',  # "5x114.3"
        r'\b[4-6]\s*bolt',
    ]
    fields["bolt_hole_count"] = any(re.search(p, html_lower) for p in bolt_patterns)
    
    # Ventilation type
    vent_patterns = [
        r'\b(vented|ventilated|ventilé|solid|plein)\b',
        r'\b(drilled|percé|slotted|rainuré)\b',
    ]
    fields["ventilation_type"] = any(re.search(p, html_lower) for p in vent_patterns)
    
    # Directionality
    directional_patterns = [
        r'directional',
        r'\b(left|right|gauche|droite)\b',
        r'(driver|passenger)\s*side',
    ]
    fields["directionality"] = any(re.search(p, html_lower) for p in directional_patterns)
    
    # Offset (less common in catalogs)
    offset_patterns = [
        r'offset[:\s]*\d{1,2}',
        r'décalage',
    ]
    fields["offset_mm"] = any(re.search(p, html_lower) for p in offset_patterns)
    
    # Weight
    weight_patterns = [
        r'weight[:\s]*\d',
        r'poids[:\s]*\d',
        r'\b\d+\s*(kg|g|lbs?)\b',
    ]
    fields["weight_kg"] = any(re.search(p, html_lower) for p in weight_patterns)
    
    # Brand (almost always present)
    brand_patterns = [
        r'\b(brembo|trw|bosch|ate|zimmermann|ferodo|pagid|textar|ebc|dba|powerstop|stoptech)\b',
        r'brand[:\s]',
        r'marque[:\s]',
    ]
    fields["brand"] = any(re.search(p, html_lower) for p in brand_patterns)
    
    # Part number / catalog reference
    partnum_patterns = [
        r'(part|item|catalog)\s*(number|ref|référence)',
        r'\b[A-Z0-9]{6,}\b',  # Alphanumeric codes
    ]
    fields["catalog_ref"] = any(re.search(p, html_lower) for p in partnum_patterns)
    
    # Vehicle fitment
    fitment_patterns = [
        r'fits\s*(19\d{2}|20\d{2})',  # "fits 2010-2015"
        r'(make|model|year)',
        r'(bmw|audi|mercedes|honda|toyota|ford|chevrolet)',
    ]
    fields["fitment_vehicle"] = any(re.search(p, html_lower) for p in fitment_patterns)
    
    return fields


def _detect_pad_fields(html: str, html_lower: str) -> Dict[str, bool]:
    """Detect pad-specific fields in HTML."""
    fields = {}
    
    # Pad shape
    fields["pad_shape"] = "pad shape" in html_lower or "forme" in html_lower
    
    # Pad thickness
    fields["pad_thickness"] = re.search(r'(pad\s*)?thickness[:\s]*\d', html_lower) is not None
    
    # Pad dimensions
    fields["pad_length"] = "length" in html_lower or "longueur" in html_lower
    fields["pad_width"] = "width" in html_lower or "largeur" in html_lower
    
    # Friction material
    material_patterns = [
        r'\b(organic|ceramic|semi-metallic|sintered)\b',
        r'friction\s*material',
        r'matériau',
    ]
    fields["friction_material"] = any(re.search(p, html_lower) for p in material_patterns)
    
    # Wear indicator
    fields["wear_indicator"] = "wear indicator" in html_lower or "témoin" in html_lower
    
    # Brand and part number (common to all)
    fields["brand"] = re.search(r'\b(ebc|ferodo|brembo|akebono|hawk)\b', html_lower) is not None
    fields["catalog_ref"] = re.search(r'(part|item)\s*(number|ref)', html_lower) is not None
    
    return fields


def _detect_vehicle_fields(html: str, html_lower: str) -> Dict[str, bool]:
    """Detect vehicle-specific fields in HTML."""
    fields = {}
    
    # Make
    make_patterns = [
        r'\b(bmw|audi|mercedes|honda|toyota|ford|chevrolet|nissan|mazda|subaru)\b',
        r'make[:\s]',
    ]
    fields["make"] = any(re.search(p, html_lower) for p in make_patterns)
    
    # Model
    fields["model"] = "model" in html_lower or "modèle" in html_lower
    
    # Year
    year_patterns = [
        r'\b(19\d{2}|20\d{2})\b',
        r'year[:\s]',
        r'année',
    ]
    fields["year"] = any(re.search(p, html_lower) for p in year_patterns)
    
    # Engine size
    engine_patterns = [
        r'\b\d\.\d\s*[Ll](iter)?',
        r'engine[:\s]*\d',
        r'moteur',
    ]
    fields["engine_size"] = any(re.search(p, html_lower) for p in engine_patterns)
    
    # Body type
    body_patterns = [
        r'\b(sedan|coupe|hatchback|wagon|suv|truck)\b',
        r'body\s*type',
    ]
    fields["body_type"] = any(re.search(p, html_lower) for p in body_patterns)
    
    # Hub specifications
    hub_patterns = [
        r'(pcd|bolt\s*circle)',
        r'hub\s*bore',
        r'center\s*bore',
    ]
    fields["hub_specs"] = any(re.search(p, html_lower) for p in hub_patterns)
    
    return fields


# ============================================================
# Main Audit Orchestration
# ============================================================

def run_audit(save_html: bool = True) -> Dict:
    """
    Run full site access audit.
    
    Args:
        save_html: Whether to save HTML samples for accessible sites
    
    Returns:
        Dict with audit results
    """
    print("="*60)
    print("MISSION 10.5 - SITE ACCESS AUDIT")
    print("="*60)
    
    # Step 1: Collect seeds
    print("\n[STEP 1] Collecting seeds from CSV files...")
    seeds = collect_seeds()
    print(f"  Found {len(seeds)} total seeds")
    
    # Group by kind
    by_kind = {}
    for seed in seeds:
        kind = seed["kind"]
        if kind not in by_kind:
            by_kind[kind] = []
        by_kind[kind].append(seed)
    
    for kind, kind_seeds in by_kind.items():
        print(f"    - {kind}: {len(kind_seeds)} seeds")
    
    # Step 2: Probe all URLs
    print("\n[STEP 2] Probing URLs for accessibility...")
    results = []
    
    for i, seed in enumerate(seeds, 1):
        print(f"\n  [{i}/{len(seeds)}] {seed['kind']}/{seed['source']}: {seed['url']}")
        result = probe_url(seed, save_html=save_html)
        
        # Print status
        if result["status_code"] == 200:
            if result["suspected_bot_protection"]:
                print(f"    -> Status {result['status_code']} BUT suspected bot protection")
            else:
                print(f"    -> Status {result['status_code']} - OK ({result['html_length']} bytes)")
                if result["html_sample_path"]:
                    print(f"    -> Saved HTML to: {result['html_sample_path']}")
        elif result["status_code"]:
            print(f"    -> Status {result['status_code']}: {result['error']}")
        else:
            print(f"    -> ERROR: {result['error']}")
        
        results.append(result)
    
    # Step 3: Analyze HTML fields for accessible sites
    print("\n[STEP 3] Analyzing HTML for field availability...")
    
    for result in results:
        if result["status_code"] == 200 and not result["suspected_bot_protection"]:
            if "_html_content" in result:
                print(f"\n  Analyzing {result['kind']}/{result['source']}...")
                fields = analyze_html_fields(result["kind"], result["_html_content"])
                result["fields_detected"] = fields
                
                # Print detected fields
                detected = [k for k, v in fields.items() if v]
                print(f"    -> Detected fields: {', '.join(detected) if detected else '(none)'}")
                
                # Remove HTML content from result (too large for JSON)
                del result["_html_content"]
            else:
                result["fields_detected"] = {}
        else:
            result["fields_detected"] = {}
    
    # Step 4: Generate summary statistics
    print("\n[STEP 4] Computing summary statistics...")
    
    summary = {
        "total_seeds": len(seeds),
        "by_kind": {},
        "domains": set(),
        "accessible_count": 0,
        "bot_protected_count": 0,
        "error_count": 0,
    }
    
    for result in results:
        kind = result["kind"]
        if kind not in summary["by_kind"]:
            summary["by_kind"][kind] = {
                "total": 0,
                "accessible": 0,
                "bot_protected": 0,
                "error": 0,
            }
        
        summary["by_kind"][kind]["total"] += 1
        summary["domains"].add(result["domain"])
        
        if result["status_code"] == 200 and not result["suspected_bot_protection"]:
            summary["accessible_count"] += 1
            summary["by_kind"][kind]["accessible"] += 1
        elif result["suspected_bot_protection"]:
            summary["bot_protected_count"] += 1
            summary["by_kind"][kind]["bot_protected"] += 1
        else:
            summary["error_count"] += 1
            summary["by_kind"][kind]["error"] += 1
    
    summary["domains"] = list(summary["domains"])
    summary["domain_count"] = len(summary["domains"])
    
    # Step 5: Save JSON report
    print("\n[STEP 5] Saving JSON report...")
    json_report = {
        "summary": summary,
        "results": results,
    }
    
    json_path = "documentation/M10_5_site_access_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False)
    
    print(f"  -> Saved JSON to: {json_path}")
    
    # Step 6: Generate Markdown report
    print("\n[STEP 6] Generating Markdown report...")
    md_path = _generate_markdown_report(summary, results)
    print(f"  -> Saved Markdown to: {md_path}")
    
    print("\n" + "="*60)
    print("AUDIT COMPLETE")
    print("="*60)
    print(f"\nSummary:")
    print(f"  - Total seeds: {summary['total_seeds']}")
    print(f"  - Unique domains: {summary['domain_count']}")
    print(f"  - Accessible (no bot protection): {summary['accessible_count']}")
    print(f"  - Bot protected: {summary['bot_protected_count']}")
    print(f"  - Errors: {summary['error_count']}")
    
    return json_report


def _generate_markdown_report(summary: Dict, results: List[Dict]) -> str:
    """Generate Markdown report from audit results."""
    lines = []
    
    lines.append("# Mission 10.5 — Site Access Audit Report")
    lines.append("")
    lines.append(f"**Date:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Summary section
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total seeds:** {summary['total_seeds']}")
    lines.append(f"- **Unique domains:** {summary['domain_count']}")
    lines.append(f"- **Accessible (no bot protection):** {summary['accessible_count']}")
    lines.append(f"- **Bot protected:** {summary['bot_protected_count']}")
    lines.append(f"- **Errors:** {summary['error_count']}")
    lines.append("")
    
    # By kind breakdown
    lines.append("### By Data Kind")
    lines.append("")
    lines.append("| Kind | Total | Accessible | Bot Protected | Errors |")
    lines.append("|------|-------|------------|---------------|--------|")
    
    for kind, stats in summary["by_kind"].items():
        lines.append(f"| **{kind}** | {stats['total']} | {stats['accessible']} | {stats['bot_protected']} | {stats['error']} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Detailed results by kind
    for kind in sorted(summary["by_kind"].keys()):
        lines.append(f"## {kind.capitalize()} Sites")
        lines.append("")
        
        kind_results = [r for r in results if r["kind"] == kind]
        
        if not kind_results:
            lines.append("*(No seeds found)*")
            lines.append("")
            continue
        
        # Table header
        lines.append("| Source | Domain | Status | Bot Protection | HTML Saved | Fields Detected |")
        lines.append("|--------|--------|--------|----------------|------------|-----------------|")
        
        for r in kind_results:
            source = r["source"]
            domain = r["domain"]
            status = r["status_code"] if r["status_code"] else "ERROR"
            bot = "Yes" if r["suspected_bot_protection"] else "No"
            html_saved = "Yes" if r["html_sample_path"] else "No"
            
            fields = r.get("fields_detected", {})
            detected = [k for k, v in fields.items() if v]
            fields_str = ", ".join(detected[:5]) if detected else "(none)"
            if len(detected) > 5:
                fields_str += f", ... ({len(detected)} total)"
            
            lines.append(f"| {source} | {domain} | {status} | {bot} | {html_saved} | {fields_str} |")
        
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Field availability analysis (for accessible sites)
    accessible_results = [r for r in results if r["status_code"] == 200 and not r["suspected_bot_protection"]]
    
    if accessible_results:
        lines.append("## Field Availability Analysis")
        lines.append("")
        lines.append("For accessible sites (no bot protection), field detection frequency:")
        lines.append("")
        
        # Aggregate field counts by kind
        field_counts = {}
        for r in accessible_results:
            kind = r["kind"]
            if kind not in field_counts:
                field_counts[kind] = {}
            
            for field, detected in r.get("fields_detected", {}).items():
                if detected:
                    field_counts[kind][field] = field_counts[kind].get(field, 0) + 1
        
        for kind in sorted(field_counts.keys()):
            lines.append(f"### {kind.capitalize()} Fields")
            lines.append("")
            
            kind_accessible = [r for r in accessible_results if r["kind"] == kind]
            total = len(kind_accessible)
            
            lines.append("| Field | Count | Percentage |")
            lines.append("|-------|-------|------------|")
            
            for field, count in sorted(field_counts[kind].items(), key=lambda x: -x[1]):
                pct = (count / total * 100) if total > 0 else 0
                lines.append(f"| {field} | {count}/{total} | {pct:.0f}% |")
            
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    # Write to file
    md_path = "documentation/M10_5_site_access_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    return md_path


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    run_audit(save_html=True)
