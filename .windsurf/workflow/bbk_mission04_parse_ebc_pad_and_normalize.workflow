# bbk_mission04_parse_ebc_pad_and_normalize.workflow
# Mission 4 — Parsing EBC pad-shapes + normalize_pad
# Status: Pending

------------------------------------------------------------
# 0. Mission Identifier
M4 — Implémenter le parseur HTML des pad-shapes EBC et la fonction normalize_pad conforme à schema_pad.json.

------------------------------------------------------------
# 1. Scope (strict)
- Implémenter / compléter deux fonctions dans `data_scraper/html_scraper.py` :
  - `parse_ebc_pad_page(html: str) -> dict`
  - `normalize_pad(raw: dict, source: str) -> dict`
- Sortie finale : un dict **normalisé** conforme à `schema_pad.json` (PadSpec).
- Ajouter les tests locaux (fichier de tests simple).
- Mettre à jour la documentation data layer pour les pads.
- Créer un log de mission.

Interdictions :
- Pas de requêtes HTTP (HTML fourni par ailleurs).
- Pas de modifications des schémas JSON.
- Pas de touche aux rotors / véhicules / hydraulique / brackets / fittings.
- Pas de refactor global de `html_scraper.py`.

------------------------------------------------------------
# 2. Fichiers (write)
- data_scraper/html_scraper.py
- test_parse_ebc_pad.py
- documentation/README_data_layer_BBK.md
- documentation/M4_parse_ebc_pad_log.md

------------------------------------------------------------
# 3. Fichiers (read-only)
- data_scraper/schema_pad.json
- documentation/MISSIONS_WIND_SURF_V1.md
- documentation/DocDeTravail_BigBrakeKit.md

------------------------------------------------------------
# 4. Tasks (séquentiel)

T1. Lire `schema_pad.json` pour connaître précisément :
  - champs requis vs optionnels,
  - types attendus (float / string / null).

T2. Inspecter `html_scraper.py` :
  - repérer si `parse_ebc_pad_page` et `normalize_pad` existent déjà,
  - sinon, créer les squelettes à proximité de `normalize_rotor` / `parse_dba_rotor_page`.

T3. Implémenter `normalize_pad(raw: dict, source: str) -> dict` :
  - helpers internes du style `safe_float(value)` si nécessaire.
  - conversions :
    - `length_mm`, `height_mm`, `thickness_mm` : string → float (retirer “mm”, espaces, etc.)
  - champs :
    - `shape_id` : EBC shape code prioritaire, sinon OEM shape clairement identifiable.
    - `swept_area_mm2` : `safe_float(raw.get("swept_area_mm2"))` ou `None`.
    - `backing_plate_type` : `raw.get("backing_plate_type")` ou `None`.
    - `brand` : `source` (ex: "EBC").
    - `catalog_ref` : code produit (ex: “DP41686R”) à partir de `raw["catalog_ref"]` ou équivalent.
  - s’assurer que tous les champs `required` du schéma sont non null.

T4. Implémenter `parse_ebc_pad_page(html: str) -> dict` :
  - utiliser BeautifulSoup pour parser le HTML (tableau specs ou liste de définitions).
  - extraire :
    - shape_id / pad shape code,
    - length_mm,
    - height_mm,
    - thickness_mm,
    - éventuellement swept_area,
    - éventuellement backing_plate_type,
    - catalog_ref (code produit).
  - construire un `raw` dict :
    ```python
    raw = {
        "shape_id": ...,
        "length_mm": ...,
        "height_mm": ...,
        "thickness_mm": ...,
        "swept_area_mm2": ...,
        "backing_plate_type": ...,
        "catalog_ref": ...,
    }
    ```
  - retourner `normalize_pad(raw, source="EBC")`.

T5. Créer `test_parse_ebc_pad.py` avec au minimum :
  - un **Smoke Test** :
    - HTML minimal avec shape_id + length/height/thickness.
    - appel à `parse_ebc_pad_page(html)` → impression du dict normalisé.
  - un **Functional Test** :
    - HTML simulé plus réaliste (table ou `<dl>` avec toutes les valeurs possibles).
    - validation contre le schéma pad (via jsonschema ou simple assert sur types + présence).

T6. Exécuter les tests (Windsurf génère les commandes) :
  - ex. :
    ```bash
    python test_parse_ebc_pad.py
    ```

T7. Mettre à jour `documentation/README_data_layer_BBK.md` :
  - ajouter sous-section “Pads — normalisation” (règles length/height/thickness, shape_id, brand, catalog_ref).
  - ajouter sous-section “Parsing EBC pad-shapes” (structure HTML, limites, multi-format éventuel).

T8. Créer `documentation/M4_parse_ebc_pad_log.md` :
  - lister fichiers modifiés,
  - décrire la logique principale de parsing/normalisation,
  - résumer les tests exécutés et leurs résultats.

T9. Git :
  - `git add` des fichiers modifiés,
  - commit avec message clair (“Mission 4: implement EBC pad parsing and normalize_pad”),
  - `git push`.

------------------------------------------------------------
# 5. Tests (attendus)

Test 1 — Smoke :
- Input : HTML simple (table ou `<dl>`) avec un seul pad EBC.
- Output : dict normalisé conforme à `schema_pad.json`.
- Vérifier :
  - `length_mm`, `height_mm`, `thickness_mm` sont bien des floats.
  - `shape_id` non vide.
  - `brand == "EBC"` ou source passé.
  - `catalog_ref` non vide.

Test 2 — Functional :
- Input : HTML simulé plus complet (avec swept_area, backing_plate_type).
- Output : dict complet respectant schéma :
  - champs optionnels présents ou `None`,
  - types stricts,
  - aucune KeyError / ValueError.

------------------------------------------------------------
# 6. Deliverables

- `parse_ebc_pad_page(html)` opérationnel.
- `normalize_pad(raw, source)` opérationnel.
- Tests `test_parse_ebc_pad.py` verts.
- Documentation data layer mise à jour.
- Log M4 créé.
- Commit et push sur GitHub.

------------------------------------------------------------
# END
