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

## 4. Ingestion (`database/ingest_pipeline.py`)

Entrée : fichiers `.jsonl` contenant des objets compatibles schémas JSON.  
Pipeline :

1. Lecture ligne à ligne.
2. `json.loads`.
3. Insertion dans la table cible via `insert_rotor` / `insert_pad` / `insert_vehicle`.
4. Commit.

V1 ne gère pas les upserts / duplicates.  
Ce sera traité dans un module ultérieur de “cleaning / dedup”.

---

## 5. Non-objectifs V1

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
