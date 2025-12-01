"""
Mission 10.4 - Real HTML Validation Script

Downloads real HTML from catalog URLs and validates parsers against actual site structure.
Generates technical report and manual checklist for human verification.
"""

import csv
import json
import os
import sys

# For HTTP requests
try:
    import urllib.request
    from urllib.error import URLError, HTTPError
except ImportError:
    print("ERROR: urllib not available")
    sys.exit(1)

# Add current dir to path for imports
sys.path.insert(0, '.')

from data_scraper.html_rotor_list_scraper import parse_rotor_list_page


def load_list_seeds():
    """Load all rotor seeds with page_type='list' from CSV."""
    seeds = []
    csv_path = "data_scraper/exporters/urls_seed_rotors.csv"
    
    print(f"[STEP 1] Loading list seeds from {csv_path}")
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            page_type = (row.get("page_type") or "").strip().lower()
            if page_type == "list":
                seeds.append({
                    "source": row.get("source", "").strip(),
                    "url": row.get("url", "").strip(),
                    "notes": row.get("notes", "").strip(),
                    "page_type": page_type,
                })
    
    print(f"  Found {len(seeds)} list seeds: {[s['source'] for s in seeds]}")
    return seeds


def download_real_html(seeds):
    """Download real HTML from each seed URL."""
    target_dir = "tests/fixtures_real/rotor_lists"
    os.makedirs(target_dir, exist_ok=True)
    
    print(f"\n[STEP 2] Downloading real HTML (saving to {target_dir})")
    
    download_results = []
    
    for seed in seeds:
        source = seed["source"]
        url = seed["url"]
        html_path = os.path.join(target_dir, f"{source}_real_01.html")
        
        result = {
            "source": source,
            "url": url,
            "notes": seed.get("notes", ""),
            "html_path": html_path,
            "status": "ok",
            "error": None,
        }
        
        print(f"\n  [{source}] Fetching {url}")
        
        try:
            # Create request with User-Agent to avoid bot blocking
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            with urllib.request.urlopen(req, timeout=20) as response:
                html_content = response.read().decode('utf-8', errors='replace')
            
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            print(f"    -> Saved to {html_path} ({len(html_content)} bytes)")
            
        except (URLError, HTTPError) as e:
            result["status"] = "error"
            result["error"] = repr(e)
            print(f"    -> ERROR: {e}")
        except Exception as e:
            result["status"] = "error"
            result["error"] = repr(e)
            print(f"    -> ERROR: {e}")
        
        download_results.append(result)
    
    return download_results


def parse_real_html(download_results):
    """Parse downloaded HTML with production parsers."""
    print(f"\n[STEP 3] Parsing real HTML with production parsers")
    
    parse_results = []
    
    for item in download_results:
        if item["status"] != "ok":
            parse_results.append({
                "source": item["source"],
                "url": item["url"],
                "notes": item["notes"],
                "html_path": item["html_path"],
                "status": "download_error",
                "error": item["error"],
                "rotor_count": 0,
                "sample": [],
                "issues": ["DOWNLOAD_ERROR"],
            })
            print(f"\n  [{item['source']}] SKIP - download failed")
            continue
        
        html_path = item["html_path"]
        source = item["source"]
        url = item["url"]
        
        print(f"\n  [{source}] Parsing {html_path}")
        
        try:
            with open(html_path, encoding="utf-8") as f:
                html = f.read()
            
            rotors = parse_rotor_list_page(html, source)
            
        except Exception as e:
            parse_results.append({
                "source": source,
                "url": url,
                "notes": item["notes"],
                "html_path": html_path,
                "status": "parser_error",
                "error": repr(e),
                "rotor_count": 0,
                "sample": [],
                "issues": ["PARSER_EXCEPTION"],
            })
            print(f"    -> PARSER ERROR: {e}")
            continue
        
        # Analyze consistency
        count = len(rotors)
        issues = []
        
        if count == 0:
            issues.append("ZERO_ROTORS")
        
        # Check critical fields on sample
        fields = ["brand", "catalog_ref", "outer_diameter_mm", "nominal_thickness_mm"]
        sample = rotors[:5]
        
        for idx, r in enumerate(sample):
            missing = [f for f in fields if not r.get(f)]
            if missing:
                issues.append(f"SAMPLE_{idx}_MISSING:{','.join(missing)}")
        
        status = "ok" if not issues else "needs_review"
        
        parse_results.append({
            "source": source,
            "url": url,
            "notes": item["notes"],
            "html_path": html_path,
            "status": status,
            "error": None,
            "rotor_count": count,
            "sample": sample,
            "issues": issues,
        })
        
        print(f"    -> Extracted {count} rotors")
        if issues:
            print(f"    -> ISSUES: {', '.join(issues)}")
        else:
            print(f"    -> OK - no issues detected")
    
    return parse_results


def generate_technical_report(parse_results):
    """Generate technical validation report."""
    print(f"\n[STEP 4] Generating technical report")
    
    lines = []
    lines.append("# Mission 10.4 — Real HTML Validation Report")
    lines.append("")
    lines.append(f"**Date:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for r in parse_results:
        lines.append(f"## Source: {r['source']}")
        lines.append("")
        lines.append(f"- **URL:** {r['url']}")
        lines.append(f"- **Notes:** {r['notes'] or '(none)'}")
        lines.append(f"- **HTML path:** `{r['html_path']}`")
        lines.append(f"- **Status:** **{r['status']}**")
        
        if r["error"]:
            lines.append(f"- **Error:** `{r['error']}`")
        
        lines.append(f"- **Rotors extracted:** **{r['rotor_count']}**")
        
        if r["issues"]:
            lines.append(f"- **Issues:** {', '.join(r['issues'])}")
        
        if r["sample"]:
            lines.append("")
            lines.append("### Sample (first up to 5 rotors):")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(r["sample"], indent=2, ensure_ascii=False))
            lines.append("```")
        
        lines.append("")
        lines.append("---")
        lines.append("")
    
    out_path = "documentation/M10_4_real_html_validation_report.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"  -> Wrote {out_path}")
    return out_path


def generate_manual_checklist(parse_results):
    """Generate manual visual checklist."""
    print(f"\n[STEP 5] Generating manual checklist")
    
    lines = []
    lines.append("# Mission 10.4 — Manual Visual Checklist")
    lines.append("")
    lines.append("> **Objectif:** Ouvrir chaque URL dans un navigateur, vérifier visuellement que quelques valeurs clés")
    lines.append("> affichées sur la page correspondent aux valeurs extraites par le scraper.")
    lines.append("> Cocher les cases au fur et à mesure.")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for r in parse_results:
        lines.append(f"## Source: {r['source']}")
        lines.append("")
        lines.append(f"- **URL:** {r['url']}")
        lines.append(f"- **Notes:** {r['notes'] or '(none)'}")
        lines.append(f"- **Rotors extraits (scraper):** **{r['rotor_count']}**")
        
        if r["status"] != "ok":
            lines.append(f"- **Status technique:** **{r['status']}** (issues: {', '.join(r['issues'])})")
        
        lines.append("")
        lines.append("### Tâches de vérification")
        lines.append("")
        lines.append("- [ ] Ouvrir l'URL dans un navigateur.")
        lines.append("- [ ] Vérifier que la page liste bien des disques de frein (rotors).")
        
        if r["rotor_count"] == 0:
            lines.append("- [ ] **IMPORTANT:** Comprendre pourquoi le scraper obtient 0 rotor.")
            lines.append("  - Possible causes: JavaScript rendering, structure HTML changée, page vide, etc.")
            lines.append("")
            lines.append("---")
            lines.append("")
            continue
        
        # Take up to 3 examples for visual validation
        examples = r["sample"][:3]
        
        for idx, ex in enumerate(examples, start=1):
            brand = ex.get("brand", "(none)")
            ref_ = ex.get("catalog_ref", "(none)")
            dia = ex.get("outer_diameter_mm", "(none)")
            thick = ex.get("nominal_thickness_mm", "(none)")
            
            lines.append(f"#### Exemple {idx}")
            lines.append("")
            lines.append(f"- [ ] Sur la page, trouver un item correspondant à:")
            lines.append(f"  - **Brand:** {brand}")
            lines.append(f"  - **Catalog ref:** {ref_}")
            lines.append(f"  - **Outer diameter (mm):** {dia}")
            lines.append(f"  - **Nominal thickness (mm):** {thick}")
            lines.append("- [ ] Vérifier que ces valeurs correspondent visuellement à ce qui est affiché.")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    out_path = "documentation/M10_4_manual_checklist.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"  -> Wrote {out_path}")
    return out_path


def run_parser_tests():
    """Re-run parser tests to ensure nothing broke."""
    print(f"\n[STEP 6] Running parser tests")
    
    import subprocess
    
    try:
        result = subprocess.run(
            ["python", "test_rotor_list_scraper.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("  -> Tests PASSED")
            return True
        else:
            print("  -> Tests FAILED")
            print(result.stdout)
            print(result.stderr)
            return False
    
    except Exception as e:
        print(f"  -> Warning: Could not run tests: {e}")
        return None


def main():
    """Main execution."""
    print("="*60)
    print("MISSION 10.4 - REAL HTML VALIDATION & CHECKLIST")
    print("="*60)
    
    # Step 1: Load seeds
    seeds = load_list_seeds()
    
    # Step 2: Download HTML
    download_results = download_real_html(seeds)
    
    # Step 3: Parse HTML
    parse_results = parse_real_html(download_results)
    
    # Step 4: Generate technical report
    tech_report = generate_technical_report(parse_results)
    
    # Step 5: Generate manual checklist
    manual_checklist = generate_manual_checklist(parse_results)
    
    # Step 6: Run tests
    tests_ok = run_parser_tests()
    
    # Summary
    print("\n" + "="*60)
    print("MISSION 10.4 COMPLETED")
    print("="*60)
    
    total_rotors = sum(r["rotor_count"] for r in parse_results)
    ok_count = sum(1 for r in parse_results if r["status"] == "ok")
    needs_review = sum(1 for r in parse_results if r["status"] == "needs_review")
    errors = sum(1 for r in parse_results if "error" in r["status"])
    
    print(f"\nResults:")
    print(f"  - Sites processed: {len(parse_results)}")
    print(f"  - OK: {ok_count}")
    print(f"  - Needs review: {needs_review}")
    print(f"  - Errors: {errors}")
    print(f"  - Total rotors extracted: {total_rotors}")
    print(f"\nReports generated:")
    print(f"  - Technical: {tech_report}")
    print(f"  - Manual: {manual_checklist}")
    
    if tests_ok:
        print(f"\n[OK] Parser tests: PASSED")
    elif tests_ok is False:
        print(f"\n[FAIL] Parser tests: FAILED")
    else:
        print(f"\n[WARN] Parser tests: Could not run")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
