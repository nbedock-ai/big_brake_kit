# bbk_mission06_normalize_vehicle_log.workflow

## Contexte

Projet : **BigBrakeKit — couche data_scraper véhicules**  
Tu exécutes **Mission 6 : Implémenter `normalize_vehicle`**.

L’état actuel :

- `parse_wheelsize_vehicle_page(html) -> raw dict` est **implémenté, testé et documenté** (M5).
- Les rotors (M2–M3) et pads (M4) ont déjà une paire `parse_*` + `normalize_*` fonctionnelle.
- Le schéma final est défini dans :  
  - `data_scraper/schema_vehicle.json`
- Les règles métier minimales de M6 sont définies dans :  
  - `MISSIONS_WIND_SURF_V1.md` (section M6 — Implémenter normalize_vehicle)
- La documentation data est centralisée dans :  
  - `documentation/README_data_layer_BBK.md`

Mission 6 doit respecter le pattern M2/M3/M4 :  
**extraction brute → normalisation typée → validation schéma + tests dédiés.**

---

## Objectif

Implémenter **`normalize_vehicle(raw: dict, source: str) -> dict`** dans `data_scraper/html_scraper.py` de façon à :

- Convertir un `raw` dict **Wheel-Size** (Mission 5) en dict **strictement conforme** à `schema_vehicle.json`.
- Gérer explicitement `source="wheelsize"` (les autres sources pourront être ajoutées plus tard).
- Manipuler les champs suivants :

Champs finaux attendus (schéma `VehicleBrakeFitment`) :

- `make: str`
- `model: str`
- `generation: str | None`
- `year_from: int`
- `year_to: int | None`
- `hub_bolt_circle_mm: float`
- `hub_bolt_hole_count: int`
- `hub_center_bore_mm: float`
- `knuckle_bolt_spacing_mm: float | None`
- `knuckle_bolt_orientation_deg: float | None`
- `max_rotor_diameter_mm: float | None`
- `wheel_inner_barrel_clearance_mm: float | None`
- `rotor_thickness_min_mm: float | None`
- `rotor_thickness_max_mm: float | None`

---

## Règles globales de travail (BigBrakeKit / Windsurf)

- **Max 100 lignes de code par bloc d’édition.**  
  Si tu dois ajouter plus, découpe en plusieurs insertions cohérentes.
- Tu dois **journaliser** les modifications dans la doc de mission dédiée.
- Tu dois **exécuter les tests** après chaque implémentation critique.
- Tu ne modifies **pas** la structure du projet ni les missions existantes hors périmètre.
- Tu ne modifies pas `parse_wheelsize_vehicle_page` (M5 est figée).

---

## Étape 1 — Lecture du contexte et cadrage

1. Ouvre et lis rapidement :

   - `data_scraper/html_scraper.py`
     - Localise :
       - La fonction `parse_wheelsize_vehicle_page`.
       - La signature placeholder de `normalize_vehicle` si elle existe déjà.
       - Les helpers déjà existants (`clean_value`, etc.).
   - `data_scraper/schema_vehicle.json`
   - `documentation/README_data_layer_BBK.md`
   - `MISSIONS_WIND_SURF_V1.md` (section “M6 — Implémenter normalize_vehicle”)
   - `test_parse_wheelsize_vehicle.py` (pour voir comment le raw est structuré).

2. Résume mentalement :

   - Quels champs `*_raw` sont présents en sortie de `parse_wheelsize_vehicle_page`.
   - Comment rotors/pads gèrent déjà la normalisation (`normalize_rotor`, `normalize_pad`) pour aligner le style.

Aucune modification de code dans cette étape.

---

## Étape 2 — Conception de `normalize_vehicle`

Avant d’écrire du code, fixe les règles de mapping pour **source="wheelsize"** :

1. **Texte :**

   - `make`, `model` :
     - Récupérer `raw["make"]`, `raw["model"]`, `strip()`.
     - Si absent ou vide → lever une exception explicite (ValueError).
   - `generation` :
     - Optionnel : `raw.get("generation")` ou `None` si vide.

2. **Années :**

   - Inputs possibles : `year_from_raw`, `year_to_raw`, `years_raw` (ex `"2016-2020"` ou `"2016-"`).
   - `year_from` :
     - Si `year_from_raw` existe → le parser en `int`.
     - Sinon, parser le début de `years_raw` avant le tiret.
     - Si impossible → exception (campo requis).
   - `year_to` :
     - Si `year_to_raw` existe → `int`.
     - Sinon :
       - Si `years_raw` est de la forme `"YYYY-YYYY"` → deuxième partie.
       - Si `"YYYY-"` ou modèle toujours en production → `None`.

3. **PCD / hub (Wheel-Size) :**

   Inputs :

   - `hub_bolt_pattern_raw` (ex `"5x114.3"`, `"5 X 112"`).
   - `hub_bolt_hole_count_raw`.
   - `hub_bolt_circle_mm_raw`.
   - `hub_center_bore_mm_raw`.

   Règles :

   - `hub_bolt_hole_count` :
     - Si `hub_bolt_hole_count_raw` → parser int.
     - Sinon, extraire avec regex sur `hub_bolt_pattern_raw` (`r"(\d+)\s*[xX]"`).
     - Si échec → exception.
   - `hub_bolt_circle_mm` :
     - Si `hub_bolt_circle_mm_raw` → parser float en mm (strip, remove "mm", remplacer "," par ".").
     - Sinon, extraire la partie après `x` dans `hub_bolt_pattern_raw`.
     - Si échec → exception.
   - `hub_center_bore_mm` :
     - Parser `hub_center_bore_mm_raw` en float mm (même helper).
     - Si échec → exception (champ requis).

4. **Rotors OEM → agrégation :**

   Inputs :

   - `front_rotor_outer_diameter_mm_raw`, `rear_rotor_outer_diameter_mm_raw`.
   - `front_rotor_thickness_mm_raw`, `rear_rotor_thickness_mm_raw`.

   Règles :

   - `max_rotor_diameter_mm` :
     - Parser toutes les valeurs disponibles en float mm.
     - Si ≥1 valeur → `max`.
     - Sinon → `None`.
   - `rotor_thickness_min_mm` / `rotor_thickness_max_mm` :
     - Parser les épaisseurs AV/AR disponibles.
     - `min` / `max` sur les valeurs non nulles.
     - Si aucune valeur → `None` pour les deux.

5. **Champs non fournis par Wheel-Size :**

   Pour `source="wheelsize"` :

   - `knuckle_bolt_spacing_mm = None`
   - `knuckle_bolt_orientation_deg = None`
   - `wheel_inner_barrel_clearance_mm = None`

6. **Schéma final :**

   Construire un dict avec **exactement** les 14 champs du schéma, en respectant types et `None` pour les optionnels.

---

## Étape 3 — Implémentation helpers de parsing (≤100 lignes par bloc)

1. Dans `data_scraper/html_scraper.py`, au même endroit que les helpers déjà utilisés par rotors/pads, ajouter si nécessaire :

   - `parse_int(value: str) -> int | None`
   - `parse_float_mm(value: str) -> float | None`  
     - `strip()`, enlever `"mm"` ou `" MM"` éventuels, remplacer `","` par `"."`, essayer `float`.

2. Respecter :

   - Aucun changement dans les fonctions déjà stables (`normalize_rotor`, `normalize_pad`, etc.), sauf si tu factorises un helper sans casser les tests existants.
   - Un bloc d’édition ≤100 lignes.

Lancer les tests existants rapides (`pytest -q` ou ciblé) pour vérifier que rotors/pads ne sont pas cassés.

---

## Étape 4 — Implémentation de `normalize_vehicle` (source="wheelsize")

1. Compléter (ou créer) dans `data_scraper/html_scraper.py` :

   ```python
   def normalize_vehicle(raw: dict, source: str) -> dict:
       ...
Logique :

Si source != "wheelsize" :

Pour l’instant : lever NotImplementedError("normalize_vehicle: unsupported source ...").

Si source == "wheelsize" :

Appliquer les règles de l’Étape 2 :

Lecture raw[...].

Parsing années.

Parsing PCD/bore.

Agrégation diamètres/épaisseurs.

Remplissage des champs None pour knuckle / clearance.

Validation interne :

Vérifier les types finaux (avec assert ou checks explicites).

Optionnel : si un validateur JSON schema existe déjà dans le projet (comme pour rotors/pads), l’appeler sur le dict final.

Respecter la limite de 100 lignes par bloc. Si nécessaire :

Bloc 1 : structure générale + extraction texte/années.

Bloc 2 : parsing PCD/bore + rotors + construction dict final.

Étape 5 — Tests dédiés normalize_vehicle
Créer test_normalize_vehicle.py à la racine du projet (au même niveau que les autres tests Mx).

Ajouter au minimum les cas suivants :

Cas 1 — Wheel-Size complet :

Civic 2016–2020 avec :

hub_bolt_pattern_raw = "5x114.3"

hub_center_bore_mm_raw = "64.1mm"

Rotors AV/AR + épaisseurs.

Vérifier :

year_from == 2016, year_to == 2020

hub_bolt_hole_count == 5

hub_bolt_circle_mm == 114.3

hub_center_bore_mm == 64.1

max_rotor_diameter_mm = max(front, rear)

rotor_thickness_min_mm / rotor_thickness_max_mm cohérents.

Cas 2 — Année ouverte :

years_raw = "2016-", pas de year_to_raw.

Attendu :

year_from == 2016

year_to is None.

Cas 3 — Sans rotors :

Aucune valeur de diamètre/épaisseur dans raw.

Attendu :

max_rotor_diameter_mm is None

rotor_thickness_min_mm is None

rotor_thickness_max_mm is None.

Cas 4 — PCD uniquement en pattern :

hub_bolt_pattern_raw = "5x112", pas de hub_bolt_hole_count_raw ni hub_bolt_circle_mm_raw.

Attendu :

hub_bolt_hole_count == 5

hub_bolt_circle_mm == 112.0.

Cas 5 — Cas invalide (PCD manquant) :

Ni pattern ni circle exploitables.

Attendu :

Exception explicite (ValueError ou similaire).

Exécuter les tests :

pytest -q ou au minimum :

pytest test_parse_wheelsize_vehicle.py test_normalize_vehicle.py

Tous les tests doivent être verts avant de passer à l’étape suivante.

Étape 6 — Documentation & Log M6
Mise à jour de la doc principale :

Dans documentation/README_data_layer_BBK.md :

Ajouter une nouvelle sous-section immédiatement après la section 3.5 (Wheel-Size RAW), par exemple :

3.6 normalize_vehicle (Wheel-Size → VehicleBrakeFitment)

Décrire :

Input : raw dict produit par parse_wheelsize_vehicle_page.

Output : dict conforme à schema_vehicle.json.

Règles principales :

Parsing années (2016-2020, 2016-).

Parsing PCD "5x114.3" → hub_bolt_hole_count, hub_bolt_circle_mm.

Parsing hub_center_bore_mm.

Agrégation diamètres/épaisseurs rotors OEM.

Champs non fournis par Wheel-Size forcés à None.

Log de mission M6 :

Créer documentation/M6_normalize_vehicle_log.md avec au minimum :

Rappel de l’objectif.

Description des règles de mapping.

Cas limites connus (ex. : records invalides → exception).

Résumé des tests (liste des cas principaux).

Référence à M5 (dépendance : parse_wheelsize_vehicle_page).

Étape 7 — Git
Vérifier l’état :

git status

Faire un commit unique et explicite, par exemple :

git commit -am "Mission 6: implement normalize_vehicle (Wheel-Size → VehicleBrakeFitment)"

Pousser vers le dépôt :

git push

Livrable final
Mission 6 est considérée TERMINÉE lorsque :

normalize_vehicle est implémentée et stable pour source="wheelsize".

Les tests de M6 (et tous les tests existants) passent.

README_data_layer_BBK.md documente le flux HTML → raw → normalized.

documentation/M6_normalize_vehicle_log.md existe et décrit clairement l’implémentation.

Le tout est committé et poussé sur le dépôt Git BigBrakeKit.

Copy code
