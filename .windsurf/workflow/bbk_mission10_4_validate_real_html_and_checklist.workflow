bbk_mission10_4_validate_real_html_and_checklist.workflow
# MISSION 10.4 — REAL HTML VALIDATION & MANUAL CHECKLIST
# Objectif:
#   1. Télécharger le HTML réel pour tous les seeds rotors avec page_type=list.
#   2. Exécuter parse_rotor_list_page(source) sur ce HTML réel.
#   3. Vérifier volume et cohérence minimale des données.
#   4. Générer deux rapports:
#      - M10_4_real_html_validation_report.md (technique)
#      - M10_4_manual_checklist.md (pour validation visuelle humaine)
#
# Contraintes:
#   - Stdlib uniquement (requests, csv, json, os, re, etc.).
#   - Pas de modification du schéma DB.
#   - Pas de navigation JS, uniquement HTML brut.
#   - On ne traite ici que les seeds rotors avec page_type="list".

steps:

  - id: load_list_seeds
    run: |
      import csv
      seeds = []
      with open("data_scraper/exporters/urls_seed_rotors.csv", newline="", encoding="utf-8") as f:
          reader = csv.DictReader(f)
          for row in reader:
              page_type = (row.get("page_type") or "").strip().lower()
              if page_type == "list":
                  seeds.append({
                      "source": row.get("source","").strip(),
                      "url": row.get("url","").strip(),
                      "notes": row.get("notes","").strip(),
                      "page_type": page_type,
                  })
      STORE("list_seeds", seeds)

  - id: download_real_html
    foreach: "${list_seeds}"
    run: |
      import os, requests
      seed = ITEM
      source = seed["source"]
      url = seed["url"]
      target_dir = "tests/fixtures_real/rotor_lists"
      os.makedirs(target_dir, exist_ok=True)

      html_path = os.path.join(target_dir, f"{source}_real_01.html")

      result = {
          "source": source,
          "url": url,
          "notes": seed.get("notes",""),
          "html_path": html_path,
          "status": "ok",
          "error": None,
      }

      try:
          resp = requests.get(url, timeout=20)
          resp.raise_for_status()
          with open(html_path, "w", encoding="utf-8") as f:
              f.write(resp.text)
      except Exception as e:
          result["status"] = "error"
          result["error"] = repr(e)

      all_results = STORE.get("download_results", [])
      all_results.append(result)
      STORE("download_results", all_results)

  - id: parse_real_html
    run: |
      import os, json
      from data_scraper.html_rotor_list_scraper import parse_rotor_list_page

      download_results = STORE.get("download_results", [])
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
              continue

          html_path = item["html_path"]
          source = item["source"]
          url = item["url"]

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
              continue

          # Analyse simple de cohérence
          count = len(rotors)
          issues = []
          if count == 0:
              issues.append("ZERO_ROTORS")

          # Vérifie champs critiques sur un petit échantillon
          fields = ["brand", "catalog_ref", "outer_diameter_mm", "nominal_thickness_mm"]
          sample = rotors[:5]
          for idx, r in enumerate(sample):
              missing = [f for f in fields if not r.get(f)]
              if missing:
                  issues.append(f"SAMPLE_{idx}_MISSING:{','.join(missing)}")

          parse_results.append({
              "source": source,
              "url": url,
              "notes": item["notes"],
              "html_path": html_path,
              "status": "ok" if not issues else "needs_review",
              "error": None,
              "rotor_count": count,
              "sample": sample,
              "issues": issues,
          })

      STORE("parse_results", parse_results)

  - id: generate_technical_report
    run: |
      import json
      results = STORE.get("parse_results", [])
      lines = []
      lines.append("# Mission 10.4 — Real HTML Validation Report")
      lines.append("")
      for r in results:
          lines.append(f"## Source: {r['source']}")
          lines.append(f"- URL: {r['url']}")
          lines.append(f"- Notes: {r['notes'] or '(none)'}")
          lines.append(f"- HTML path: `{r['html_path']}`")
          lines.append(f"- Status: **{r['status']}**")
          if r["error"]:
              lines.append(f"- Error: `{r['error']}`")
          lines.append(f"- Rotors extracted: **{r['rotor_count']}**")
          if r["issues"]:
              lines.append(f"- Issues: {', '.join(r['issues'])}")
          if r["sample"]:
              lines.append("")
              lines.append("Sample (first up to 5 rotors):")
              lines.append("```json")
              lines.append(json.dumps(r["sample"], indent=2, ensure_ascii=False))
              lines.append("```")
          lines.append("")
          lines.append("---")
          lines.append("")

      out_path = "documentation/M10_4_real_html_validation_report.md"
      with open(out_path, "w", encoding="utf-8") as f:
          f.write("\n".join(lines))
      print(f"Wrote technical report to {out_path}")

  - id: generate_manual_checklist
    run: |
      import json

      results = STORE.get("parse_results", [])
      lines = []
      lines.append("# Mission 10.4 — Manual Visual Checklist")
      lines.append("")
      lines.append("> Objectif: ouvrir chaque URL dans un navigateur, vérifier visuellement que quelques valeurs clés affichées sur la page")
      lines.append("> correspondent aux valeurs extraites par le scraper. Cocher les cases au fur et à mesure.")
      lines.append("")

      for r in results:
          lines.append(f"## Source: {r['source']}")
          lines.append("")
          lines.append(f"- URL: {r['url']}")
          lines.append(f"- Notes: {r['notes'] or '(none)'}")
          lines.append(f"- Rotors extraits (scraper): **{r['rotor_count']}**")
          if r["status"] != "ok":
              lines.append(f"- Status technique: **{r['status']}** (issues: {', '.join(r['issues'])})")
          lines.append("")
          lines.append("### Tâches de vérification")
          lines.append("")
          lines.append("- [ ] Ouvrir l'URL dans un navigateur.")
          lines.append("- [ ] Vérifier que la page liste bien des disques de frein (rotors).")
          if r["rotor_count"] == 0:
              lines.append("- [ ] Comprendre pourquoi le scraper obtient 0 rotor (JS, changement de structure, etc.).")
              lines.append("")
              lines.append("---")
              lines.append("")
              continue

          # On prend jusqu'à 3 exemples à valider visuellement
          examples = r["sample"][:3]
          for idx, ex in enumerate(examples, start=1):
              brand = ex.get("brand")
              ref_ = ex.get("catalog_ref")
              dia = ex.get("outer_diameter_mm")
              thick = ex.get("nominal_thickness_mm")
              lines.append(f"#### Exemple {idx}")
              lines.append("")
              lines.append(f"- [ ] Sur la page, trouver un item correspondant à:")
              lines.append(f"  - Brand: **{brand}**")
              lines.append(f"  - Catalog ref: **{ref_}**")
              lines.append(f"  - Outer diameter (mm): **{dia}**")
              lines.append(f"  - Nominal thickness (mm): **{thick}**")
              lines.append("- [ ] Vérifier que ces valeurs correspondent visuellement à ce qui est affiché.")
              lines.append("")

          lines.append("---")
          lines.append("")

      out_path = "documentation/M10_4_manual_checklist.md"
      with open(out_path, "w", encoding="utf-8") as f:
          f.write("\n".join(lines))
      print(f"Wrote manual checklist to {out_path}")

  - id: run_parser_tests
    run: |
      import subprocess
      # Optionnel: revalider les tests unitaires du module de list scraping
      try:
          subprocess.run(["python", "test_rotor_list_scraper.py"], check=True)
      except Exception as e:
          print("Warning: test_rotor_list_scraper.py failed:", e)
