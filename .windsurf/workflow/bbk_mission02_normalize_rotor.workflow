# bbk_mission02_normalize_rotor.workflow
# Mission 2 — Implémenter normalize_rotor
# Status: Pending

------------------------------------------------------------
# 0. Mission Identifier
M2 — Implémenter une fonction normalize_rotor stable, propre, entièrement conforme au schéma JSON rotor.

------------------------------------------------------------
# 1. Scope (strict)
- Modifier UNE SEULE fonction : `normalize_rotor` dans `data_scraper/html_scraper.py`.
- Aucun autre fichier modifié sauf :
  - `documentation/README_data_layer_BBK.md` (mise à jour obligatoire)
  - `documentation/MISSIONS_WIND_SURF_V1.md` (si nécessaire)
- Implémentation stricte de la normalisation.
- Conversion types (float, int).
- Standardisation ventilation_type, directionality.
- Calcul offset_mm si absent.
- Null pour les champs optionnels.
- Validation JSON.

Interdictions :
- Aucune modification du parsing.
- Aucune modification des schémas JSON.
- Aucune logique hydraulique, bracket ou fittings.

------------------------------------------------------------
# 2. Fichiers (write)
- data_scraper/html_scraper.py
- documentation/README_data_layer_BBK.md
- documentation/M2_normalize_rotor_log.md

------------------------------------------------------------
# 3. Fichiers (read-only)
- data_scraper/schema_rotor.json
- documentation/MISSIONS_WIND_SURF_V1.md
- documentation/DocDeTravail_BigBrakeKit.md

------------------------------------------------------------
# 4. Tasks (séquentiel)
T1. Ouvrir `schema_rotor.json` et analyser les champs obligatoires/optionnels.  
T2. Analyser la fonction `normalize_rotor` existante.  
T3. Implémenter une normalisation complète :
  - parse mm → float  
  - ventilation_type in {solid, vented, drilled, slotted, drilled_slotted}  
  - directionality in {non_directional, left, right}  
  - compute offset_mm = overall_height_mm - hat_height_mm  
  - brand = source  
  - catalog_ref = raw[“ref”] ou None  
  - toutes les valeurs absentes → None  
T4. Ajouter validation JSON (test code fourni dans la mission).  
T5. Production du test smoke :
python - <<EOF
from data_scraper.html_scraper import normalize_rotor
sample = {"outer_diameter_mm":"330","nominal_thickness_mm":"28","hat_height_mm":"46","overall_height_mm":"52","center_bore_mm":"64.1","bolt_circle_mm":"114.3","bolt_hole_count":"5","ventilation_type":"vented","directionality":"non_directional","ref":"TEST123"}
print(normalize_rotor(sample,"dba"))
EOF

diff
Copy code
T6. Produire 2 tests fonctionnels supplémentaires.  
T7. Mettre à jour `README_data_layer_BBK.md` :
- section “Normalisation rotors”  
- rappel des règles offset_mm + conversions  
T8. Générer `documentation/M2_normalize_rotor_log.md`.  
T9. Git add + commit + push.

------------------------------------------------------------
# 5. Tests
- Smoke test = absence d’erreur Python.  
- Functional tests = 2 entrées brutes différentes validées contre le schéma JSON.  
- Vérification offset calculé correctement.

------------------------------------------------------------
# 6. Deliverables
- Fonction normalize_rotor opérationnelle et stable.
- Documentation mise à jour.
- Log complet.
- Commit + push Git.

------------------------------------------------------------
# END