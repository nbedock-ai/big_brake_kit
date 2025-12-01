# bbk_mission03_parse_dba_rotor.workflow
# Mission 3 — HTML Parsing for DBA Rotors
# Status: Pending

------------------------------------------------------------
# 0. Mission Identifier
M3 — Implémenter le parseur HTML pour les rotors DBA et produire un rotor normalisé via normalize_rotor.

------------------------------------------------------------
# 1. Scope (strict)
- Modifier uniquement `data_scraper/html_scraper.py`.
- Implémenter la fonction `parse_dba_rotor_page(html: str) -> dict`.
- Extraire les attributs bruts depuis un HTML DBA.
- Nettoyer les strings (strip “mm”, “Ø”, espaces).
- Construire un `raw_dict` complet.
- Appeler `normalize_rotor(raw, source="dba")`.
- Retourner l’objet normalisé.

Interdictions :
- Aucun scraping HTTP.  
- Aucun changement dans normalize_rotor.  
- Aucun changement dans les schémas JSON.  
- Aucun lien avec véhicules / brackets / hydraulique.

------------------------------------------------------------
# 2. Fichiers (write)
- data_scraper/html_scraper.py
- documentation/README_data_layer_BBK.md
- documentation/M3_parse_dba_rotor_log.md

------------------------------------------------------------
# 3. Fichiers (read-only)
- data_scraper/schema_rotor.json
- documentation/MISSIONS_WIND_SURF_V1.md
- documentation/DocDeTravail_BigBrakeKit.md

------------------------------------------------------------
# 4. Tasks (séquentiel)

T1. Analyse structurelle d’une page produit DBA (titres, tableaux, labels).  
T2. Implémenter une extraction HTML robuste :
  - BeautifulSoup obligatoire.
  - Extraction table/key-value.
  - Nettoyage de texte (remove “mm”, “Ø”, tabs).
T3. Construire `raw` :
raw = {
"outer_diameter_mm": ...,
"nominal_thickness_mm": ...,
"hat_height_mm": ...,
"overall_height_mm": ...,
"center_bore_mm": ...,
"bolt_circle_mm": ...,
"bolt_hole_count": ...,
"ventilation_type": ...,
"directionality": ...,
"ref": ...,
}

bash
Copy code
T4. Appeler `normalize_rotor(raw, "dba")`.  
T5. Vérifier la validité JSON via test code.  
T6. Générer test smoke + test fonctionnel :

Smoke:
html = "<html> ... table with values ... </html>"
from data_scraper.html_scraper import parse_dba_rotor_page
print(parse_dba_rotor_page(html))

diff
Copy code

Test fonctionnel :
- Simuler un HTML avec diameter, thickness, vented, non-directional.
- Vérifier output via validation JSON (jsonschema).

T7. Mise à jour `README_data_layer_BBK.md` (section parsing rotors → sous-section DBA).  
T8. Générer `M3_parse_dba_rotor_log.md`.  
T9. Git add + commit + push.

------------------------------------------------------------
# 5. Tests

Test 1 = Smoke Test  
- HTML simplifié contenant 3–5 champs.  
- parse_dba_rotor_page renvoie un dict normalisé.  
- Aucun crash.

Test 2 = Functional test  
- HTML simulé comprenant tous les champs.  
- Comparaison avec le schéma rotor.  
- offset_mm correct.  
- enums corrects.  
- catalog_ref correct.

------------------------------------------------------------
# 6. Deliverables
- Fonction parse_dba_rotor_page opérationnelle.
- Extraction HTML robuste.
- Output normalisé 100% conforme au schéma rotor.
- Documentation mise à jour.
- Log mission.
- Commit Git.

------------------------------------------------------------