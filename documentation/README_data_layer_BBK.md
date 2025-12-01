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

## 2. Base SQL (`database/init.sql`)

Trois tables :

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
