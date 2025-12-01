MISSIONS_WIND_SURF_V1.md
BigBrakeKit — Missions Windsurf (V1)

Pipeline complet de scraping → normalisation → ingestion → analyse rotors maîtres.

Ce document décrit toutes les missions que Windsurf doit exécuter, dans l’ordre, chacune isolée dans un bloc ≤100 lignes de code, sans déviation du périmètre.

Les chemins de fichiers sont exacts et vérifiés.

M0 — Boot & Chargement du Projet
Objectif

Vérifier que Windsurf peut :

charger l’arborescence complète du projet,

lire les fichiers critiques existants,

exécuter le projet localement.

Fichiers à vérifier

data_scraper/html_scraper.py

data_scraper/vision_scraper.py

database/init.sql

database/ingest_pipeline.py

data_seed_url.txt

data_scraper/schema_rotor.json

data_scraper/schema_pad.json

data_scraper/schema_vehicle.json

Livrable

Log d’environnement + confirmation de non-erreurs.

M1 — Implémenter parse_dba_rotor_page
Fichier cible

data_scraper/html_scraper.py

Objectif

Parser les pages DBA (HTML tables) → produire une liste de dicts « raw ».

Contraintes

Extraire : outer_diameter_mm, nominal_thickness_mm, hat_height_mm, overall_height_mm, bolt_circle_mm, bolt_hole_count.

Aucune normalisation ici.

Aucun hardcoding d’un modèle spécifique.

Livrable

Fonction opérationnelle testée sur 3–5 URLs DBA du data_seed_url.txt.

M2 — Implémenter normalize_rotor
Fichier

data_scraper/html_scraper.py

Objectif

Convertir raw → dict conforme schema_rotor.json.

Règles

conversion float/int systématique

ventilation_type et directionality normalisés

offset_mm = overall_height_mm - hat_height_mm si absent

champs optionnels → null si absent

Livrable

Fonction stable, testée via 2–3 exemples.

M3 — Implémenter parse_brembo_rotor_page
Fichier

data_scraper/html_scraper.py

Objectif

Parser les tableaux Brembo basés sur <table>.

Livrable

List[dict] raw, compatible avec M2.

M4 — Implémenter parse_ebc_pad_page + normalize_pad
Fichier

data_scraper/html_scraper.py

Objectif

Scraper les pad-shapes EBC.

Règles

extraire length_mm / height_mm / thickness_mm

shape_id = identifiant EBC (ou OEM quand visible)

map → schema_pad.json

Livrable

Fonctions testées sur 2–3 shapes du seed URL.

M5 — Implémenter parse_wheelsize_vehicle_page
Fichier

data_scraper/html_scraper.py

Objectif

Extraire pour chaque modèle :

hub_bolt_circle_mm

hub_bolt_hole_count

hub_center_bore_mm

years

éventuellement rotor OEM diameter (si présent)

Livrable

List[dict] raw.

M6 — Implémenter normalize_vehicle
Fichier

data_scraper/html_scraper.py

Objectif

Convertir raw → schema_vehicle.json.

Règles

PCD format "5x114.3" → { bolt_hole_count:5, hub_bolt_circle_mm:114.3 }

années string → integer

valeurs absentes → null

Livrable

Fonction prête à ingestion.

M7 — Implémenter pipeline ingest_all()
Fichier

database/ingest_pipeline.py

Objectif

Pipeline unique :

Lire data_seed_url.txt.

Groupes : rotors / pads / vehicles.

Pour chaque URL :

fetch_html()

parse_*()

normalize_*()

Générer un .jsonl par type.

Appeler ingest_jsonl().

Livrable

Pipeline stable, testable.

M8 — Script CLI scrape_and_ingest.py
Objectif

Créer un binaire simple qui exécute M7.

Fonctionnalités

--only rotors

--only pads

--only vehicles

--all

Fichier

Nouveau : scrape_and_ingest.py à la racine du projet.

M9 — Déduplication V1
Fichier

database/ingest_pipeline.py

Objectif

Éviter les doublons naïfs.

Règles

rotors : même (brand, catalog_ref) → skip

pads : même (shape_id, brand, catalog_ref) → skip

vehicle : même (make, model, year_from) → skip

Livrable

Filtre intégré avant insertion DB.

M10 — Analyse préliminaire des rotors
Fichier

rotor_analysis/clustering.py

Objectif

Regrouper les rotors selon :

outer_diameter_mm

nominal_thickness_mm

offset_mm

ventilation_type (encodée)

Livrable

Cluster labels + distances.

M11 — Sélection des 15–25 rotors maîtres
Fichier

rotor_analysis/select_master_rotors.py

Objectif

Sélectionner 1 rotor représentatif par cluster.

Livrable

master_rotors.json.

M12 — Documentation V1
Fichiers

documentation/README_data_layer_BBK.md

documentation/DocDeTravail_BigBrakeKit.md

Objectif

Mettre à jour avec :

pipeline complet,

dépendances M1–M11,

coverage des limites.

M13 — Préparation Vision (V2)
Fichier

data_scraper/vision_scraper.py

Objectif

Préparer prompts pour extraction :

Zimmermann PDF

StopTech PDF

Knuckle geometry

Livrable

Prompts commentés + TODO list.

M14 — Test End-to-End
Objectif

Tester l’intégralité du pipeline :

Scraping (M1–M5)

Normalisation (M2, M4, M6)

.jsonl (M7)

Ingestion (M7)

Clustering (M10)

Master rotors (M11)

Livrable

Log complet + validation du flux.

M15 — Préparation Caliper V1
Objectif

Définir la roadmap pour l’étape suivante : design paramétrique 2P / 4P / 6P.

Fichier

caliper_design/CALIPER_MISSIONS.md

Livrable

Liste structurée des missions CAO.

## M16 — Préparation du module hydraulique (V2)

Objectif :
- créer `hydraulics/segments.json` définissant trois plages de surface de pistons (S, M, L),
- créer `hydraulics/vehicle_segment_map.json` pour associer les véhicules ou familles de véhicules à ces segments,
- préparer un fichier `hydraulics/README_hydraulics.md` exposant la logique de correspondance.

Aucune donnée de pression ou de diamètre de durite n’est collectée. 
Le fitting hydraulique sera traité via un catalogue restreint de standards (M10x1, M10x1.25, etc.) et non via scraping.
