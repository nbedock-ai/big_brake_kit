# bbk_mission05_parse_wheelsize_vehicle.workflow
# Mission 5 — HTML Parsing for Wheel-Size Vehicle Pages
# Status: Pending

------------------------------------------------------------
# 0. Mission Identifier
M5 — Implémenter le parseur HTML pour les pages véhicule Wheel-Size
et produire un dict brut prêt pour normalize_vehicle (Mission 6).

------------------------------------------------------------
# 1. Scope (strict)
- Ajouter / compléter UNE fonction dans `data_scraper/html_scraper.py` :
  - `parse_wheelsize_vehicle_page(html: str) -> dict`
- La fonction :
  - reçoit un HTML (string),
  - parse la structure (table, définitions, attributs data-*),
  - extrait les champs véhicule / moyeu / roues,
  - renvoie un **raw dict** (strings / nombres bruts, pas encore conforme au schéma).
- Aucune normalisation finale ici (pas de float/int systématiques, pas de validation JSON).

Interdictions :
- Aucun HTTP, aucune requête réseau.
- Aucune modification de `schema_vehicle.json`.
- Aucune création ou modification de `normalize_vehicle` (Mission 6).
- Aucune logique hydraulique / bracket / fittings.

------------------------------------------------------------
# 2. Fichiers (write)
- data_scraper/html_scraper.py
- test_parse_wheelsize_vehicle.py
- documentation/README_data_layer_BBK.md
- documentation/M5_parse_wheelsize_vehicle_log.md

------------------------------------------------------------
# 3. Fichiers (read-only)
- data_scraper/schema_vehicle.json
- documentation/MISSIONS_WIND_SURF_V1.md
- documentation/DocDeTravail_BigBrakeKit.md

------------------------------------------------------------
# 4. Tasks (séquentiel)

T1. Lire `schema_vehicle.json` pour comprendre :
  - champs liés au moyeu (PCD, bore),
  - champs véhicule (make, model, year_from/year_to),
  - ce qui sera normalisé plus tard (Mission 6).

T2. Ouvrir `data_scraper/html_scraper.py` :
  - localiser l’endroit où ajouter `parse_wheelsize_vehicle_page`,
  - réutiliser les patterns de parsing déjà en place (BeautifulSoup, clean_value, etc.).

T3. Implémenter `parse_wheelsize_vehicle_page(html: str) -> dict` :
  - Utiliser BeautifulSoup.
  - Supporter au moins :
    - un format `table` (spécifications en lignes `<tr><th>Label</th><td>Value</td>`),
    - un format `definition list` (`<dl><dt>Label</dt><dd>Value</dd>`),
    - des attributs `data-*` si nécessaire.
  - Extraire au minimum, en bruts (pas encore typés) :

    ```python
    raw = {
        "make": ...,
        "model": ...,
        "generation": ...,
        "year_from_raw": ...,
        "year_to_raw": ...,

        "hub_bolt_pattern_raw": ...,    # ex: "5x114.3"
        "hub_bolt_hole_count_raw": ...,
        "hub_bolt_circle_mm_raw": ...,
        "hub_center_bore_mm_raw": ...,

        "front_wheel_width_in_raw": ...,
        "front_wheel_diameter_in_raw": ...,
        "rear_wheel_width_in_raw": ...,
        "rear_wheel_diameter_in_raw": ...,

        "front_tire_dimensions_raw": ...,
        "rear_tire_dimensions_raw": ...,

        "front_rotor_outer_diameter_mm_raw": ...,
        "front_rotor_thickness_mm_raw": ...,
        "rear_rotor_outer_diameter_mm_raw": ...,
        "rear_rotor_thickness_mm_raw": ...
    }
    ```

  - Les champs que Wheel-Size ne fournit pas peuvent être omis ou mis à `None` dès cette étape.

T4. Créer `test_parse_wheelsize_vehicle.py` :
  - **Smoke Test** :
    - HTML minimal avec make/model/years + PCD + bore.
    - Appel à `parse_wheelsize_vehicle_page(html)`.
    - Assertions :
      - `raw["make"]`, `raw["model"]` non vides,
      - `raw["hub_bolt_pattern_raw"]` = "5x114.3",
      - `raw["hub_center_bore_mm_raw"]` match attendu.
  - **Functional Test** :
    - HTML simulé plus riche (front/rear wheels, tires, rotors).
    - Vérifier que tous les champs *_raw attendus sont présents et non vides.

T5. Exécuter les tests :
  - `python test_parse_wheelsize_vehicle.py`
  - Corriger jusqu’à ce que tous les tests passent.

T6. Mettre à jour `documentation/README_data_layer_BBK.md` :
  - Ajouter sous-section dans la partie “Vehicles” :
    - “Parsing Wheel-Size vehicle pages”
    - lister les champs bruts extraits,
    - préciser que la normalisation type/valeurs se fait en Mission 6.

T7. Créer `documentation/M5_parse_wheelsize_vehicle_log.md` :
  - Fichiers modifiés,
  - Structure du raw dict,
  - Résumé des tests.

T8. Git :
  - `git add` des fichiers modifiés,
  - `git commit -m "Mission 5: implement parse_wheelsize_vehicle_page (Wheel-Size HTML parser)"`,
  - `git push`.

------------------------------------------------------------
# 5. Tests (attendus)

Test 1 — Smoke :
- HTML minimal avec table contenant :
  - Make, Model, Years, PCD, Center Bore.
- `parse_wheelsize_vehicle_page` renvoie un dict avec :
  - `make`, `model`, `year_from_raw`, `year_to_raw`,
  - `hub_bolt_pattern_raw`, `hub_center_bore_mm_raw`.

Test 2 — Functional :
- HTML simulé avec sections front/rear wheels + tires + rotor size.
- Tous les champs *_raw listés en T3 présents et non vides.
- Aucune exception.

------------------------------------------------------------
# 6. Deliverables

- Fonction `parse_wheelsize_vehicle_page(html)` opérationnelle.
- Fichier de tests `test_parse_wheelsize_vehicle.py` avec 2 tests verts.
- README data layer documentant l’extraction Wheel-Size.
- Log M5.
- Commit + push GitHub.

------------------------------------------------------------
# END
