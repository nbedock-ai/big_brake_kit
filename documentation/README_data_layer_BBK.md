# BigBrakeKit – Couche Données (V1)

## 0. Objectif

Construire une **base de données minimaliste mais exploitable** pour :

1. Sélectionner une **banque de rotors maîtres** (15–25 références).
2. Dimensionner les **étriers universels** (2P / 4P / 6P) autour d’une plaquette maître.
3. Générer des **brackets CNC** corrects du premier coup.

Scope de cette doc :  
- schémas JSON (rotors / plaquettes / véhicules),  
- structure SQL,  
- plan du scraper HTML V1,  
- pipeline d’ingestion.

Aucun design CAO, aucun bracket ici.

---

## 1. Schémas JSON

### 1.1 Rotors (`schema_rotor.json`)

Variables **obligatoires** (produit bloquant si manquantes) :

- `outer_diameter_mm`
- `nominal_thickness_mm`
- `hat_height_mm`
- `overall_height_mm`
- `center_bore_mm`
- `bolt_circle_mm` (PCD)
- `bolt_hole_count`
- `ventilation_type` (`solid`, `vented`, etc.)
- `directionality` (`non_directional`, `left`, `right`)
- `brand`
- `catalog_ref`

Variables **optionnelles** (prises si dispo) :

- `offset_mm` (sinon déductible via `overall_height - hat_height`)
- `rotor_weight_kg`
- `mounting_type` (`1_piece`, `2_piece_bolted`, `2_piece_floating`)
- `oem_part_number`
- `pad_swept_area_mm2`

Usage : clustering, couverture diamètres/épaisseurs/offsets, sélection des rotors maîtres.

---

### 1.2 Plaquettes (`schema_pad.json`)

Obligatoires :

- `shape_id`
- `length_mm`
- `height_mm`
- `thickness_mm`
- `brand`
- `catalog_ref`

Optionnels :

- `swept_area_mm2`
- `backing_plate_type`

Usage : définition stricte de la plaquette maître qui contraint la géométrie interne des étriers.

---

### 1.3 Véhicules (`schema_vehicle.json`)

Obligatoires :

- `make`
- `model`
- `generation` (nullable)
- `year_from`, `year_to`
- `hub_bolt_circle_mm`
- `hub_bolt_hole_count`
- `hub_center_bore_mm`

Optionnels (V2+ ou collecte partiellement manuelle) :

- `knuckle_bolt_spacing_mm`
- `knuckle_bolt_orientation_deg`
- `max_rotor_diameter_mm`
- `wheel_inner_barrel_clearance_mm`
- `rotor_thickness_min_mm`
- `rotor_thickness_max_mm`

Usage : mapping véhicule → espace des rotors possibles → sélection d’un rotor maître + design du bracket.

---

### 1.4 Normalisation Rotors (`normalize_rotor`)

**Status: ✅ Implémenté (Mission 2)**

La fonction `normalize_rotor` dans `data_scraper/html_scraper.py` transforme les données brutes (strings) en objets conformes au schéma JSON.

**Règles de normalisation:**

1. **Conversion de types:**
   - Champs numériques (mm) → `float`
   - `bolt_hole_count` → `int`
   - Valeurs absentes ou invalides → `None`

2. **Standardisation des enums:**
   - `ventilation_type`: "drilled/slotted" → "drilled_slotted", etc.
   - `directionality`: "non-directional" → "non_directional", "l" → "left", "r" → "right"
   - `mounting_type`: "2-piece_bolted" → "2_piece_bolted", etc.

3. **Calcul automatique de `offset_mm`:**
   ```python
   offset_mm = overall_height_mm - hat_height_mm
   ```
   Si `offset_mm` est déjà fourni dans les données brutes, il est préservé.

4. **Champs obligatoires vs optionnels:**
   - Champs obligatoires: doivent être présents et non-null après normalisation
   - Champs optionnels: peuvent être `None`

5. **Brand et catalog_ref:**
   - `brand` = `source` (argument de la fonction)
   - `catalog_ref` = `raw["ref"]` ou `raw["catalog_ref"]` ou chaîne vide

**Exemple:**
```python
raw = {"outer_diameter_mm": "330", "nominal_thickness_mm": "28", ...}
normalized = normalize_rotor(raw, "dba")
# offset_mm sera automatiquement calculé si absent
```

---

### 1.5 Normalisation Plaquettes (`normalize_pad`)

**Status: ✅ Implémenté (Mission 4)**

La fonction `normalize_pad` convertit les données brutes de plaquettes en objets conformes à `schema_pad.json`.

**Règles de normalisation:**

1. **Conversion dimensions** (string → float)
   - `length_mm`, `height_mm`, `thickness_mm`
   - Nettoyage automatique: suppression "mm", "²", espaces
   - Valeurs invalides → `None`

2. **Shape ID**
   - Priorité: `raw["shape_id"]` ou `raw["shape"]`
   - Codes EBC typiques: "FA123", "256", "21234"
   - Requis: ne peut pas être vide

3. **Champs optionnels**
   - `swept_area_mm2`: float ou `None` (nettoyage "mm²")
   - `backing_plate_type`: string ou `None` (ex: "Steel", "Aluminum")

4. **Brand et catalog_ref**
   - `brand`: provient du paramètre `source` (ex: "ebc")
   - `catalog_ref`: `raw["catalog_ref"]` ou `raw["ref"]` ou `raw["part_number"]`
   - Codes EBC typiques: "DP41686R", "FA256R"

**Exemple:**
```python
raw = {
    "shape_id": "FA123",
    "length_mm": "100.5mm",
    "height_mm": "45.2",
    "thickness_mm": "15.0",
    "catalog_ref": "DP41686R"
}
pad = normalize_pad(raw, source="ebc")
# Returns: {"shape_id": "FA123", "length_mm": 100.5, ...}
```

---

## 2. Structure SQL

Tables :

- `rotors`
- `pads`
- `vehicles`

Contraintes :

- types alignés sur les schémas JSON,  
- colonnes optionnelles nullable,  
- aucun foreign key strict pour la V1 (liaisons logiques faites plus tard dans le module analyse).

DB cible : SQLite (simple à manipuler depuis Python, suffisant pour V1/V2).

---

## 3. Scraper HTML V1 (`data_scraper/html_scraper.py`)

### 3.1 Cible V1

**Rotors :**

- **DBA** : HTML avec specs complètes (diamètre, épaisseur, hat height, offset, ventilation…)
- **Brembo** : HTML avec diamètre, épaisseur, hauteur, PCD, trous.

**Plaquettes :**

- **EBC** : catalogue par pad-shape, dimensions exposées en clair.

**Véhicules :**

- **Wheel-Size.com** : PCD + centre bore + tailles de roues + parfois dimensions de disques OEM.

### 3.2 Fonctions prévues (squelette existant)

- `fetch_html(url) -> str`
- `parse_dba_rotor_page(html) -> list[dict]`
- `parse_brembo_rotor_page(html) -> list[dict]`
- `parse_ebc_pad_page(html) -> list[dict]`
- `parse_wheelsize_vehicle_page(html) -> list[dict]`
- `normalize_rotor(raw, source) -> dict`
- `normalize_pad(raw, source) -> dict`
- `normalize_vehicle(raw, source) -> dict`

Principe :  
- `parse_*` reste proche du HTML brut (colonnes, labels).  
- `normalize_*` produit des objets strictement conformes aux schémas JSON.

### 3.3 Parsing DBA Rotors (`parse_dba_rotor_page`)

**Status: ✅ Implémenté (Mission 3)**

La fonction `parse_dba_rotor_page` extrait les spécifications d'un rotor depuis une page produit DBA et retourne un objet normalisé.

**Stratégies d'extraction (multi-méthodes):**

1. **Tables HTML** (`<table>` avec `<tr><td>Label</td><td>Value</td></tr>`)
   - Méthode principale pour la plupart des pages produit
   - Détecte automatiquement les labels de spécifications

2. **Listes de définitions** (`<dl>/<dt>/<dd>`)
   - Alternative courante pour pages de catalogue
   - Mapping flexible des termes techniques

3. **Attributs data** (`data-diameter`, `data-thickness`, etc.)
   - Pour pages modernes avec données structurées

**Nettoyage automatique:**
- Suppression unités: "mm", "Ø", "°"
- Normalisation espaces et caractères spéciaux
- Mapping variations de labels (ex: "Centre Bore" → "center_bore_mm")

**Extraction catalog_ref:**
- Recherche pattern DBA (ex: "DBA42134S", "DBA52930XD")
- Préfère le code le plus long/spécifique dans le titre
- Fallback sur éléments `.product-code`

**Inférence ventilation_type:**
- Détecte mots-clés dans titre: "slotted", "drilled", "vented"
- Combine "drilled and slotted" → "drilled_slotted"
- Default: "vented" si non spécifié

**Exemple:**
```python
html = "<html><h1>DBA 4000 T3 Slotted DBA42134S</h1>...</html>"
rotor = parse_dba_rotor_page(html)
# Returns normalized dict with all fields typed correctly
```

**Tests validés:**
- ✅ Extraction table HTML
- ✅ Extraction definition list
- ✅ Calcul automatique offset_mm
- ✅ Inférence ventilation depuis titre
- ✅ Extraction catalog_ref (codes complets)

---

### 3.4 Parsing EBC Pads (`parse_ebc_pad_page`)

**Status: ✅ Implémenté (Mission 4)**

La fonction `parse_ebc_pad_page` extrait les spécifications de plaquettes depuis une page produit EBC et retourne un objet normalisé.

**Stratégies d'extraction (multi-méthodes):**

1. **Tables HTML** (`<table>` avec `<tr><td>Label</td><td>Value</td></tr>`)
   - Labels reconnus: "Shape ID", "Shape Code", "Length", "Height", "Thickness"
   - Détection automatique des champs optionnels (swept area, backing plate)

2. **Listes de définitions** (`<dl>/<dt>/<dd>`)
   - Mapping flexible: "Shape" → `shape_id`, "Length" → `length_mm`
   - Gère les variations de labels

3. **Attributs data** (`data-shape`, `data-length`, etc.)
   - Pour HTML moderne avec données structurées

**Nettoyage automatique:**
- Suppression unités: "mm", "mm²", "²"
- Normalisation espaces et caractères spéciaux

**Extraction catalog_ref:**
- Recherche patterns EBC: "DP####XX", "FA####XX"
- Fallback sur éléments `.product-code`
- Fallback sur lignes "Part Number" / "Reference"

**Extraction shape_id:**
- Tables: labels contenant "shape"
- Titre: pattern "Shape: [CODE]"
- Valeur requise pour validation schéma

**Exemple:**
```python
html = "<html><h1>EBC Redstuff DP41686R</h1><table>...</table></html>"
pad = parse_ebc_pad_page(html)
# Returns normalized dict with all fields typed correctly
```

**Tests validés:**
- ✅ Extraction table HTML
- ✅ Extraction definition list
- ✅ Champs optionnels (swept area, backing plate)
- ✅ Nettoyage unités (mm, mm²)
- ✅ Extraction catalog_ref (codes complets)

---

### 3.5 Parsing Wheel-Size Vehicles (`parse_wheelsize_vehicle_page`)

**Status: ✅ Implémenté (Mission 5)**

La fonction `parse_wheelsize_vehicle_page` extrait les spécifications véhicule depuis une page Wheel-Size et retourne un **dict brut** (non normalisé).

**⚠️ Important:** Cette fonction retourne des données **RAW** (brutes). La normalisation (conversion types, validation schéma) se fera dans `normalize_vehicle` (Mission 6).

**Stratégies d'extraction (multi-méthodes):**

1. **Tables HTML** (`<table>` avec `<tr><th>Label</th><td>Value</td></tr>`)
   - Labels reconnus: Make, Model, Generation, Year From/To, PCD, Center Bore
   - Supporte front/rear wheel, tire, rotor specifications

2. **Listes de définitions** (`<dl>/<dt>/<dd>`)
   - Mapping simple pour données structurées
   - Gère variations de labels

3. **Attributs data** (`data-make`, `data-model`, `data-pcd`, `data-bore`)
   - Pour HTML moderne avec métadonnées structurées

4. **Titre/H1 fallback**
   - Extrait Make/Model depuis `<h1>` si absent des tables
   - Pattern: "Honda Civic 2016-2020"

**Champs extraits (raw, avec suffixe _raw):**

**Identification véhicule:**
- `make`, `model`, `generation`
- `year_from_raw`, `year_to_raw`, `years_raw`

**Spécifications moyeu:**
- `hub_bolt_pattern_raw` (ex: "5x114.3")
- `hub_bolt_hole_count_raw` (parsé depuis pattern)
- `hub_bolt_circle_mm_raw` (parsé depuis pattern)
- `hub_center_bore_mm_raw`

**Roues avant/arrière:**
- `front_wheel_width_in_raw`, `front_wheel_diameter_in_raw`
- `rear_wheel_width_in_raw`, `rear_wheel_diameter_in_raw`

**Pneus:**
- `front_tire_dimensions_raw` (ex: "225/45R17")
- `rear_tire_dimensions_raw`

**Rotors OEM:**
- `front_rotor_outer_diameter_mm_raw`, `front_rotor_thickness_mm_raw`
- `rear_rotor_outer_diameter_mm_raw`, `rear_rotor_thickness_mm_raw`

**Parsing automatique bolt pattern:**
```python
# "5x114.3" →
{
    "hub_bolt_pattern_raw": "5x114.3",
    "hub_bolt_hole_count_raw": "5",
    "hub_bolt_circle_mm_raw": "114.3"
}
```

**Exemple:**
```python
html = "<html><table><tr><th>PCD</th><td>5x120</td></tr>...</table></html>"
raw = parse_wheelsize_vehicle_page(html)
# Returns: {"hub_bolt_pattern_raw": "5x120", ...}
# NOT normalized - strings avec unités préservées
```

**Tests validés:**
- ✅ Extraction table HTML (9 champs)
- ✅ Extraction complète (19 champs: véhicule + roues + pneus + rotors)
- ✅ Extraction definition list
- ✅ Fallback titre/H1 pour Make/Model
- ✅ Parsing automatique bolt pattern (5x114.3 → composants)

**Note:** Les unités sont **préservées** dans les champs _raw (ex: "64.1mm", "7.5 inches"). La conversion et le nettoyage se feront en Mission 6 (`normalize_vehicle`).

---

### 3.6 Normalisation Véhicules (`normalize_vehicle`)

**Status: ✅ Implémenté (Mission 6)**

La fonction `normalize_vehicle` convertit les données RAW de Mission 5 en objets conformes à `schema_vehicle.json`.

**Pipeline complet:**
```python
HTML → parse_wheelsize_vehicle_page() → raw dict (strings + unités)
     → normalize_vehicle() → typed dict (schema-compliant)
```

**Règles de normalisation pour source="wheelsize":**

**1. Identification véhicule (requis):**
- `make`, `model`: Extraction depuis `raw["make"]`, `raw["model"]`
  - Si absent ou vide → ValueError
- `generation`: Optionnel, `raw["generation"]` ou `None`

**2. Années (year_from requis, year_to optionnel):**
- Stratégies multiples:
  - Priorité 1: `year_from_raw` / `year_to_raw` explicites
  - Priorité 2: Parse `years_raw` avec regex
    - Format "2016-2020" → year_from=2016, year_to=2020
    - Format "2017-" → year_from=2017, year_to=None (véhicule en production)
- Conversion: string → `int`
- Si year_from impossible à parser → ValueError

**3. Spécifications moyeu (requis):**

**hub_bolt_hole_count et hub_bolt_circle_mm:**
- Stratégie 1: Champs explicites
  - `hub_bolt_hole_count_raw` → int
  - `hub_bolt_circle_mm_raw` → float (nettoyage "mm")
- Stratégie 2: Parse depuis `hub_bolt_pattern_raw`
  - Regex: `r"(\d+)\s*[xX]\s*([\d.]+)"`
  - "5x114.3" → hole_count=5, circle_mm=114.3
- Si échec → ValueError (champs requis)

**hub_center_bore_mm:**
- Parse `hub_center_bore_mm_raw` en float
- Nettoyage automatique: supprime "mm", "MM", remplace "," par "."
- Si échec → ValueError (champ requis)

**4. Rotors OEM (optionnels - agrégation):**

Inputs:
- `front_rotor_outer_diameter_mm_raw`, `rear_rotor_outer_diameter_mm_raw`
- `front_rotor_thickness_mm_raw`, `rear_rotor_thickness_mm_raw`

Outputs:
- `max_rotor_diameter_mm`: `max()` des diamètres AV/AR disponibles, ou `None`
- `rotor_thickness_min_mm`: `min()` des épaisseurs, ou `None`
- `rotor_thickness_max_mm`: `max()` des épaisseurs, ou `None`

**5. Champs non fournis par Wheel-Size:**
- `knuckle_bolt_spacing_mm = None`
- `knuckle_bolt_orientation_deg = None`
- `wheel_inner_barrel_clearance_mm = None`

**Exemple de normalisation:**
```python
raw = {
    "make": "Honda",
    "model": "Civic",
    "year_from_raw": "2016",
    "year_to_raw": "2020",
    "hub_bolt_pattern_raw": "5x114.3",
    "hub_center_bore_mm_raw": "64.1mm",
    "front_rotor_outer_diameter_mm_raw": "300mm",
    "rear_rotor_outer_diameter_mm_raw": "282mm"
}

vehicle = normalize_vehicle(raw, "wheelsize")
# Returns:
{
    "make": "Honda",
    "model": "Civic",
    "year_from": 2016,              # int
    "year_to": 2020,                # int
    "hub_bolt_hole_count": 5,       # parsed from pattern
    "hub_bolt_circle_mm": 114.3,    # parsed from pattern
    "hub_center_bore_mm": 64.1,     # float, mm stripped
    "max_rotor_diameter_mm": 300.0, # max of front/rear
    "knuckle_bolt_spacing_mm": None,
    ...
}
```

**Gestion des erreurs:**
- `ValueError`: Champs requis manquants ou non parsables
- `NotImplementedError`: Source non supportée (seulement "wheelsize" pour l'instant)

**Tests validés:**
- ✅ Normalisation complète avec rotors OEM
- ✅ Année ouverte "2017-" → year_to=None
- ✅ Sans rotors OEM → champs optionnels=None
- ✅ PCD depuis champs explicites vs pattern
- ✅ Erreurs: make/model manquants
- ✅ Erreurs: PCD manquant
- ✅ Erreurs: source non supportée
- ✅ Parse années depuis "2018-2022"

Total: 32 assertions validées

---

## 4. Ingestion (`database/ingest_pipeline.py`)

**Status:** Implémenté (Mission 7)

### 4.1 Pipeline Principal - `ingest_all()`

Point d'entrée unique pour l'ingestion de toutes les données depuis les seeds URL.

**Architecture:**
```python
CSV Seeds → ingest_all() → Scrapers → Normalizers → SQLite DB
```

**Flux complet:**
1. Lecture des fichiers seed CSV depuis `data_seed_url.txt`
2. Itération sur les URLs par groupe (rotors, pads, vehicles)
3. Pour chaque URL:
   - Fetch HTML avec `fetch_html(url)`
   - Parse avec `parse_*_page(html)`
   - Normalize avec `normalize_*(raw, source)`
   - Validate champs requis
   - Insert dans DB avec `insert_*(conn, obj)`
4. Commit et statistiques finales

**Utilisation:**
```python
# Ingérer tous les groupes
from database.ingest_pipeline import ingest_all
ingest_all()

# Ingérer un groupe spécifique
ingest_all(group="vehicles")
ingest_all(group="rotors")
ingest_all(group="pads")
```

**CLI:**
```bash
# Tout ingérer
python -m database.ingest_pipeline

# Groupe spécifique
python -m database.ingest_pipeline vehicles
python -m database.ingest_pipeline rotors
python -m database.ingest_pipeline pads
```

### 4.2 Format des Seeds

**Structure CSV:**
```csv
source,url,notes
dba,https://www.dba.com.au/product/...,note explicative
wheel-size,https://www.wheel-size.com/size/honda/civic/,example family
```

**Fichiers seed:**
- `data_scraper/exporters/urls_seed_rotors.csv` → Rotors DBA/Brembo
- `data_scraper/exporters/urls_seed_pads.csv` → Pads EBC
- `data_scraper/exporters/urls_seed_vehicles.csv` → Vehicles Wheel-Size

**Index:** `data_seed_url.txt` référence tous les CSV actifs

### 4.3 Helpers d'Ingestion

**load_seed_csv_paths():**
- Parse `data_seed_url.txt`
- Retourne dict: `{"rotors": [paths], "pads": [paths], "vehicles": [paths]}`

**iter_seed_urls(kind: str):**
- Itère sur les URLs d'un groupe
- Yield: `(source, url, notes)`

**process_rotor_seed(conn, source, url):**
- Fetch → parse_dba_rotor_page → validate → insert
- Retourne nombre d'insertions (0 ou 1)

**process_pad_seed(conn, source, url):**
- Fetch → parse_ebc_pad_page → validate → insert

**process_vehicle_seed(conn, source, url):**
- Fetch → parse_wheelsize_vehicle_page → normalize_vehicle → validate → insert

### 4.4 Gestion des Erreurs

**Par URL:**
- Try/catch autour de chaque fetch/parse/insert
- Erreurs loggées dans console
- Pipeline continue (ne s'arrête jamais)
- Compteur d'erreurs dans statistiques finales

**Validation avant insertion:**
- Reject: None, dict vide, champs requis manquants
- Pas de déduplication intelligente (sera M9)

### 4.5 Ingestion JSONL (Legacy)

**ingest_jsonl(path, table):**
Entrée : fichiers `.jsonl` contenant des objets compatibles schémas JSON.  
Pipeline :

1. Lecture ligne à ligne
2. `json.loads`
3. Insertion dans la table cible via `insert_rotor` / `insert_pad` / `insert_vehicle`
4. Commit

**Note:** V1 ne gère pas les upserts / duplicates.  
Ce sera traité dans un module ultérieur de "cleaning / dedup".

### 4.6 Tests Validés

**test_ingest_pipeline.py:**
- load_seed_csv_paths - parse data_seed_url.txt
- iter_seed_urls - itère sur CSV seeds
- insert_* functions - insertion DB en mémoire
- Schema validation - tables rotors/pads/vehicles

Total: 14 assertions validées

**Integration tests:**
Nécessitent accès réseau, à lancer manuellement:
```bash
python -m database.ingest_pipeline vehicles
```

### 4.7 CLI Script - scrape_and_ingest.py

**Status: ✅ Implémenté (Mission 8)**

Script wrapper simplifié à la racine du projet pour piloter `ingest_all()` depuis la ligne de commande.

**Localisation:** `scrape_and_ingest.py` (racine du projet)

**Syntaxe:**
```bash
# Ingérer tous les groupes (comportement par défaut)
python scrape_and_ingest.py

# Sélection explicite du groupe
python scrape_and_ingest.py --only all        # Tous les groupes
python scrape_and_ingest.py --only rotors     # Rotors uniquement
python scrape_and_ingest.py --only pads       # Pads uniquement
python scrape_and_ingest.py --only vehicles   # Vehicles uniquement
```

**Arguments:**
- `--only` : Choix du groupe à ingérer
  - Valeurs possibles : `all`, `rotors`, `pads`, `vehicles`
  - Défaut : `all` (si omis)

**Mapping vers ingest_all:**
- `--only all` ou sans argument → `ingest_all(group=None)` - ingère tout
- `--only rotors` → `ingest_all(group="rotors")` - rotors uniquement
- `--only pads` → `ingest_all(group="pads")` - pads uniquement
- `--only vehicles` → `ingest_all(group="vehicles")` - vehicles uniquement

**Implémentation:**
- Utilise `argparse` pour parsing des arguments
- Fonction `main(argv)` testable (accepte liste d'args pour tests unitaires)
- Logging minimaliste (affichage groupe cible + confirmation)

**Tests validés:**
- ✅ Sans argument → groupe=None
- ✅ --only all → groupe=None
- ✅ --only rotors → groupe='rotors'
- ✅ --only pads → groupe='pads'
- ✅ --only vehicles → groupe='vehicles'

Total: 10 assertions validées (test_scrape_and_ingest_cli.py)

**Exemple d'utilisation:**
```bash
# Ingérer seulement les véhicules depuis seeds
python scrape_and_ingest.py --only vehicles
```

**Output:**
```
[CLI] Starting ingestion for: vehicles
============================================================
BIGBRAKEKIT - INGESTION PIPELINE
============================================================
...
[VEHICLE] ✓ Inserted: Honda Civic (2016-2020)
...
[CLI] Ingestion complete
```

**Avantages CLI vs Python API:**
- Facilite automatisation shell/batch
- Pas besoin d'ouvrir Python REPL
- Meilleur pour scripts cron/CI-CD
- Interface unifiée pour utilisateurs non-développeurs

### 4.8 Déduplication V1

**Status: ✅ Implémenté (Mission 9)**

Déduplication simple basée sur des clés primaires pour éviter les doublons lors de l'ingestion.

**Stratégie:** Vérification DB avant insertion (SELECT check)

**Clés de déduplication:**

| Type | Clé de déduplication | Champs |
|------|---------------------|--------|
| **Rotors** | `(brand, catalog_ref)` | Identifiant unique par fabricant + référence catalogue |
| **Pads** | `(shape_id, brand, catalog_ref)` | Shape + identifiant fabricant |
| **Vehicles** | `(make, model, year_from)` | Marque + modèle + année début génération |

**Fonctionnement:**
1. Avant chaque insertion, vérification via `*_exists(conn, obj)`
2. Si l'entrée existe déjà → skip avec log `○ Duplicate ...`
3. Si l'entrée n'existe pas → insertion normale

**Implémentation:**
```python
# Helpers de vérification
def rotor_exists(conn, rotor: dict) -> bool:
    sql = "SELECT 1 FROM rotors WHERE brand = ? AND catalog_ref = ? LIMIT 1"
    return conn.execute(sql, (rotor["brand"], rotor["catalog_ref"])).fetchone() is not None

# Intégration dans process_*_seed
if rotor_exists(conn, rotor):
    print("[ROTOR] ○ Duplicate {brand}/{catalog_ref}, skipping")
    return 0  # Ne compte pas comme insertion
insert_rotor(conn, rotor)
return 1  # Insertion réussie
```

**Impact:**
- `ingest_all()` devient **idempotent** : relancer le pipeline ne crée pas de doublons
- Seeds partiellement recoupants ne génèrent pas de duplicates
- Compteur d'insertions reflète les nouvelles entrées uniquement

**Comportement observable:**
```
[ROTOR] Fetching dba: https://...
[ROTOR] ✓ Inserted: DBA DBA2000    # Premier passage

[ROTOR] Fetching dba: https://...
[ROTOR] ○ Duplicate DBA/DBA2000, skipping    # Deuxième passage (même seed)
```

**Limitations V1:**
- **Pas de déduplication "floue"** : comparaison exacte uniquement
- **Pas de merge** : si données légèrement différentes, aucune mise à jour
- **Pas de versionning** : dernière version n'écrase pas l'ancienne
- **Pas de cross-type dedup** : rotor vs pad avec même ref ne sont pas comparés

**Tests validés:**
- ✅ Rotor duplicate insert blocked (same brand + catalog_ref)
- ✅ Pad duplicate insert blocked (same shape_id + brand + catalog_ref)
- ✅ Vehicle duplicate insert blocked (same make + model + year_from)
- ✅ Non-duplicates allowed (different keys)

Total: 11 assertions validées (test_dedup_v1.py)

**Évolutions futures (hors V1):**
- M10+: Déduplication floue (Levenshtein distance sur catalog_ref)
- M11+: Merge automatique (mise à jour champs optionnels manquants)
- M12+: Versionning (garder historique des modifications)

---

## 5. Analyse des rotors (Mission 10)

### 5.1 Analyse préliminaire des rotors - Clustering géométrique

**Status: ✅ Implémenté (Mission 10)**

Segmentation de l'espace des rotors en familles géométriques pour faciliter la sélection de rotors maîtres (M11).

**Objectif:**
- Grouper les rotors similaires géométriquement
- Préparer la base pour sélectionner 15-25 rotors maîtres représentatifs
- Identifier la couverture de l'espace des rotors disponibles

**Fichier:** `rotor_analysis/clustering.py`

**Méthode: Clustering par binning** (V1 - pas de k-means)

Au lieu d'algorithmes complexes, on utilise un binning simple sur 3 dimensions géométriques:

| Dimension | Pas de binning | Justification |
|-----------|---------------|---------------|
| **Diamètre externe** | 5mm | Groupes naturels (280, 285 → bin 280) |
| **Épaisseur nominale** | 0.5mm | Précision nécessaire (22.0 vs 22.5mm) |
| **Offset** | 2mm | Tolérance raisonnable pour montage |

**Calcul de l'offset effectif:**
```python
# Stratégie 1: Offset explicite
if rotor["offset_mm"] is not None:
    offset = rotor["offset_mm"]

# Stratégie 2: Calcul depuis hauteurs
elif rotor["overall_height_mm"] and rotor["hat_height_mm"]:
    offset = overall_height_mm - hat_height_mm

# Stratégie 3: Incomplet
else:
    offset = None  # Rotor skippé du clustering
```

**Algorithme de binning:**
```python
def bin_value(x: float, step: float) -> float:
    return round(x / step) * step

# Exemple: 282.3mm avec step=5mm → 280mm
# Exemple: 287.8mm avec step=5mm → 290mm
```

**Clé de cluster:**
Chaque rotor est mappé à une clé `(diameter_bin, thickness_bin, offset_bin)`.

Exemple:
- Rotor A: (282.3mm, 22.4mm, 45mm) → key = (280, 22.5, 44)
- Rotor B: (280.0mm, 22.0mm, 40mm) → key = (280, 22.0, 40)
- → Rotors dans clusters différents

**Output: rotor_clusters.json**

Structure:
```json
{
  "meta": {
    "diam_bin_step_mm": 5.0,
    "thick_bin_step_mm": 0.5,
    "offset_bin_step_mm": 2.0,
    "cluster_count": 15
  },
  "clusters": [
    {
      "cluster_id": 0,
      "key": {
        "outer_diameter_mm": 280.0,
        "nominal_thickness_mm": 22.0,
        "offset_mm": 40.0
      },
      "centroid": {
        "outer_diameter_mm": 281.2,
        "nominal_thickness_mm": 22.1,
        "offset_mm": 40.3
      },
      "count": 3,
      "members": [
        {"brand": "DBA", "catalog_ref": "DBA2000", ...},
        ...
      ]
    },
    ...
  ]
}
```

**Centroïde:**
Moyenne arithmétique des membres du cluster (pas pondérée).

**Usage:**
```bash
# Direct Python
python -m rotor_analysis.clustering

# Ou import
from rotor_analysis.clustering import run_clustering
run_clustering()
```

**Tests validés:**
- ✅ Binning function (5 cas, arrondi correct)
- ✅ Offset calculation (explicit, calculated, incomplete)
- ✅ Cluster key generation (complete, calculated, incomplete)
- ✅ Cluster building (grouping, count, centroids)
- ✅ JSON serialization (meta, clusters, structured format)

Total: 26 assertions validées (test_rotor_clustering.py)

**Lien avec M11:**
Ce clustering servira de base pour:
1. Identifier les zones denses (rotors populaires)
2. Identifier les zones creuses (rotors rares/spécialisés)
3. Sélectionner 15-25 rotors maîtres représentatifs
4. Couvrir uniformément l'espace géométrique

**Limitations V1:**
- **Pas de pondération:** Tous les rotors comptent également
- **Pas de clustering avancé:** Binning simple, pas de k-means/DBSCAN
- **Pas d'analyse de disponibilité:** Ne considère pas stock/popularité
- **Pas d'utilisation du poids:** `rotor_weight_kg` ignoré

**Évolutions futures (V2):**
- M11: Sélection de rotors maîtres depuis clusters
- M12+: K-means ou DBSCAN pour clusters adaptatifs
- M13+: Pondération par popularité/disponibilité
- M14+: Features supplémentaires (poids, ventilation type)

---

### 5.2 Expansion massive des seeds rotors (Mission 10.1)

**Status: ✅ Implémenté (Mission 10.1)**

Extension du catalogue de sources de données pour multiplier le volume de rotors disponibles avant la sélection de rotors maîtres (M11).

**Objectif:**
- Enrichir la base de données avec une diversité maximale de rotors
- Couvrir différents segments de marché (OEM, aftermarket, performance, racing)
- Préparer un dataset suffisamment large pour M11 (sélection 15-25 maîtres)

**Fichier modifié:** `data_scraper/exporters/urls_seed_rotors.csv`

**Nouvelles sources ajoutées (24 URLs):**

#### Aftermarket généraliste
- **AutoDoc UK** - Fournisseur aftermarket européen
- **Mister-Auto** - Plateforme aftermarket européenne
- **CarParts.com** - Aftermarket US
- **PartsGeek** - Aftermarket US
- **AutoZone** - Chaîne retail US

#### Spécialistes performance
- **Summit Racing** - Performance parts retailer
- **FCP Euro** - Spécialiste voitures européennes
- **StopTech** - Spécialiste freinage performance
- **PowerStop** - Kits freinage performance
- **Wilwood** - Freinage racing

#### Fabricants OEM/OE
- **Otto Zimmermann** - Fabricant OE allemand
- **Centric Parts** - Pièces de remplacement OE
- **Wagner Brake** - Qualité OE aftermarket
- **Raybestos** - Fournisseur OE
- **TRW Aftermarket** - Marque OE aftermarket
- **Bosch Automotive** - Bosch freinage
- **ACDelco** - Pièces OE GM

#### OEM constructeurs
- **Ford Parts** - Pièces OEM Ford
- **Mopar** - Pièces OEM Chrysler/Dodge/Jeep

#### Racing/Motorsport
- **AP Racing** - Freinage motorsport
- **Ferodo Racing** - Produits freinage course
- **EBC Brakes** - Gamme performance/racing

#### Fabricants spécialisés
- **Brembo Europe** - Catalogue OEM Brembo complet
- **DBA Australia** - Catalogue principal DBA

**Impact attendu:**
- **Avant M10.1:** ~4 seed URLs → volume limité de rotors
- **Après M10.1:** 28 seed URLs → couverture géographique et segmentaire maximale

**Segmentation marché couverte:**

| Segment | Sources | Couverture |
|---------|---------|-----------|
| **OEM/OE quality** | Zimmermann, Centric, Wagner, Raybestos, TRW, Bosch, ACDelco | ✅ Complete |
| **OEM constructeurs** | Ford, Mopar | ✅ US brands |
| **Aftermarket retail** | AutoDoc, Mister-Auto, CarParts, PartsGeek, AutoZone | ✅ EU + US |
| **Performance street** | StopTech, PowerStop, EBC, DBA | ✅ Complete |
| **Racing** | Wilwood, AP Racing, Ferodo, Brembo | ✅ Complete |
| **Spécialistes** | FCP Euro, Summit Racing | ✅ Niches |

**Zones géographiques:**
- 🇪🇺 **Europe:** AutoDoc UK, Mister-Auto, Brembo EU, Zimmermann, TRW
- 🇺🇸 **USA:** CarParts, PartsGeek, Summit, AutoZone, Ford, Mopar
- 🇦🇺 **Australia:** DBA
- 🌍 **International:** Bosch, ACDelco, Wilwood, AP Racing

**Déduplication garantie:**
Grâce à M9 (déduplication V1), les rotors avec même `(brand, catalog_ref)` ne sont pas dupliqués même si présents dans plusieurs sources.

**Usage:**
```bash
# Scraping avec seeds étendus
python scrape_and_ingest.py --only rotors

# Le pipeline M7 + M9:
# 1. Lit urls_seed_rotors.csv (28 seeds)
# 2. Scrape chaque URL
# 3. Parse et normalise
# 4. Déduplique (M9)
# 5. Insère dans DB
```

**Bénéfices pour M11:**
1. **Diversité géométrique:** Rotors de 250-400mm, 18-34mm épaisseur
2. **Couverture applications:** Compact, midsize, SUV, sport, racing
3. **Variété marques:** OEM, premium, budget, racing
4. **Robustesse clusters (M10):** Clusters avec plus de membres = centroids plus représentatifs

**Limitations connues:**
- Certaines URLs peuvent être des landing pages nécessitant navigation supplémentaire
- Pagination pas toujours automatique (peut nécessiter seeds spécifiques par page)
- Sites dynamiques (JavaScript) peuvent nécessiter scraping avancé (hors scope V1)

**Évolutions futures:**
- M10.2: Scraping multi-list (parcours automatique pagination)
- M10.3: Scraping systématique par véhicules (URLs spécifiques make/model)
- M10.4: Scraping PDF catalogs (Zimmermann, StopTech) via Vision

---

## 6. Non-objectifs V1

Explicitement hors scope pour l’instant :

- scraping PDF (Zimmermann, StopTech) → sera géré par Vision,
- extraction automatique des specs de knuckles,
- enrichissement thermiques (températures max, capacités thermiques),
- normalisation inter-marques des codes références.

---

## 6. Pré-requis avant missions Windsurf

Pour que Windsurf puisse travailler proprement :

1. **Les 3 schémas JSON doivent être figés** (fait).
2. **`init.sql` et `ingest_pipeline.py` doivent être en place** (fait).
3. **`html_scraper.py` doit exister avec toutes les signatures de fonctions** (fait).
4. **Les fichiers de seed URLs doivent être créés** (cf. section suivante dans le projet).

Les missions Windsurf pourront ensuite être formulées sur cette base, sans ambiguïté de structure.


## 7. Extension future — Données hydrauliques (V2)

Les étriers 2P/4P/6P nécessitent une correspondance entre la surface totale de pistons et le maître-cylindre du véhicule. Cette relation n'est pas couverte dans la version actuelle de la base de données.

Une extension V2 ajoutera :
- un fichier `hydraulics/segments.json` définissant 2–3 plages hydrauliques cibles (S, M, L) exprimées en surface totale de pistons (mm²),
- un fichier `hydraulics/vehicle_segment_map.json` associant chaque véhicule à l’un de ces segments,
- une table optionnelle `fittings` listant les standards de banjo/raccord utilisés pour fabriquer des durites sur mesure.

Aucune donnée de pression, diamètre de durite ou pression nominale ne sera collectée : ces valeurs ne sont pas pertinentes pour la conception du kit. La seule variable hydraulique pertinente est la surface totale de pistons.


## 8. Catalogue de fittings (durites)

Afin de garantir la compatibilité hydraulique, la V2 du projet introduira un petit catalogue de standards de raccords :
- M10x1 banjo
- M10x1.25 banjo
- M12x1 banjo
- filetage direct conique (inverted flare)

Ces standards ne sont pas liés au véhicule : une durite sur mesure sera fournie avec le kit. La base de données V1 n’a pas besoin d’intégrer ces informations.

## Portée hydraulique exacte du projet

Pour garantir une sensation de pédale correcte après le passage 2P → 4P ou 4P → 6P, le projet utilisera des surfaces hydrauliques d’étriers adaptées par segment. La pression de ligne, le diamètre de durite et les valeurs OEM de pression ne sont pas modélisées. Seule compte la surface totale des pistons dans l’étrier.

La base V1 reste centrée sur : rotors, plaquettes, géométrie véhicule.
La base V2 ajoutera : hydraulique segmentée et catalogue de fittings.

---

## 9. Données additionnelles implémentées (V1.1)

**Status: ✅ Implémenté**

Les couches suivantes ont été ajoutées à la structure du projet :

### **9.1 Hydraulics**
- `hydraulics/segments.json` - Définition des segments S/M/L (surface pistons)
- `hydraulics/vehicle_segment_map.json` - Mapping véhicule → segment hydraulique
- `hydraulics/README_hydraulics.md` - Documentation hydraulique
- `caliper_design/hydraulic_config.json` - Configuration pistons par étrier et segment

### **9.2 Bracket Geometry**
- `bracket_geometry/schema_bracket_geometry.json` - Schéma JSON des variables géométriques
- `bracket_geometry/normalize_bracket_geometry.py` - Normalisation des données raw
- `bracket_geometry/README_bracket_geometry.md` - Documentation

Variables couvertes :
- Espacement boulons knuckle, orientation, offset rotor
- Dégagements (roue, étrier), diamètres/épaisseurs rotors
- Type de montage (axial/radial)

### **9.3 Brake Line Fittings**
- `fittings/catalog.json` - Standards de raccords (M10x1, M10x1.25, M12x1, inverted flare)
- `fittings/README_fittings.md` - Documentation

Ces couches sont prêtes pour les missions M2-M16.
