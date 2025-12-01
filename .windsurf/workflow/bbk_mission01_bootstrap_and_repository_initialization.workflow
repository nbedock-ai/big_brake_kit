# bbk_mission01_bootstrap_and_repository_initialization.workflow
# BigBrakeKit — Mission 1
# Project Bootstrap and Repository Initialization
# Status: Pending
# Author: Windsurf SSR

------------------------------------------------------------
# 0. Mission Identifier
M1 — Repository Bootstrap: directory scaffold, file placement, context loading.

------------------------------------------------------------
# 1. Scope (strict)
- Créer l’arborescence complète du projet BigBrakeKit.
- Déplacer tous les fichiers existants dans leur répertoire final.
- Aucune modification de code Python.
- Aucune modification de schémas JSON.
- Aucun scraping.
- Aucun traitement hydraulique.
- Uniquement structure + préparation environnementale.

Interdictions :
- Pas de refactor.
- Pas d’introduction de nouvelles dépendances.
- Pas d’édition de code source existant.
- Pas d’ajout de TODO.
- Pas de logique business.

------------------------------------------------------------
# 2. Inputs (direct)
Fichiers fournis dans la session :
- DocDeTravail_BigBrakeKit.md      (documentation produit)
- README_data_layer_BBK.md         (documentation couche données)
- MISSIONS_WIND_SURF_V1.md         (missions M0–M16)
- schema_rotor.json
- schema_pad.json
- schema_vehicle.json
- html_scraper.py
- vision_scraper.py
- ingest_pipeline.py
- init.sql
- data_seed_url.txt

Référence obligatoire (lecture seule) :
- ProtocoleWindsurf_v1.md      (règles SSR, contraintes strictes)  :contentReference[oaicite:0]{index=0}
- readme_cascade_v2.md         (configuration locale Windsurf/Cascade)  :contentReference[oaicite:1]{index=1}

------------------------------------------------------------
# 3. Repository Target Structure
Créer exactement l’arborescence suivante :

big_brake_kit/
├── data_scraper/
│   ├── html_scraper.py
│   ├── vision_scraper.py
│   ├── schema_rotor.json
│   ├── schema_pad.json
│   ├── schema_vehicle.json
│   └── exporters/
│       ├── urls_seed_rotors.csv
│       ├── urls_seed_pads.csv
│       └── urls_seed_vehicles.csv
├── database/
│   ├── init.sql
│   ├── ingest_pipeline.py
│   └── models/
├── rotor_analysis/
│   ├── clustering.py           (placeholder vide)
│   └── select_master_rotors.py (placeholder vide)
├── caliper_design/
│   ├── notes/
├── bracket_generator/
│   ├── compute_offsets.py      (placeholder vide)
│   ├── generate_bracket_parametric.py (placeholder vide)
│   └── outputs/
├── documentation/
│   ├── DocDeTravail_BigBrakeKit.md
│   ├── README_data_layer_BBK.md
│   └── MISSIONS_WIND_SURF_V1.md
└── data_seed_url.txt

Aucun autre répertoire.  
Aucune variation permise.

------------------------------------------------------------
# 4. Read-Only Context (DOIT être chargé par Windsurf)
Windsurf doit ouvrir en lecture :
- documentation/DocDeTravail_BigBrakeKit.md :contentReference[oaicite:2]{index=2}
- documentation/README_data_layer_BBK.md   :contentReference[oaicite:3]{index=3}
- documentation/MISSIONS_WIND_SURF_V1.md   :contentReference[oaicite:4]{index=4}
- data_scraper/schema_rotor.json           :contentReference[oaicite:5]{index=5}
- data_scraper/schema_pad.json             :contentReference[oaicite:6]{index=6}
- data_scraper/schema_vehicle.json         :contentReference[oaicite:7]{index=7}

Objectif : charger le contexte fonctionnel global avant la suite des missions M1–M11.

------------------------------------------------------------
# 5. Preconditions
- L’arborescence finale n’existe pas ou est incomplète.
- Aucun fichier ne doit être écrasé sans vérification.
- Tous les documents hydrauliques nouveaux (sections hydrauliques dans DocDeTravail) doivent être pris en compte conceptuellement mais ne modifient pas la structure V1.
- Aucune dépendance installée.
- Python ≥ 3.10 disponible.

------------------------------------------------------------
# 6. Tasks (séquentiel, strict)
T1. Créer les répertoires (mkdir -p) exactement comme définis dans la section 3.  
T2. Déplacer chaque fichier fourni dans son emplacement final.  
T3. Générer les trois CSV seed (rotors/pads/vehicles) à partir de `data_seed_url.txt`.  
T4. Vérifier la présence physique de tous les fichiers critiques.  
T5. Ouvrir en onglets dans Windsurf les fichiers suivants :  
    - DocDeTravail_BigBrakeKit.md  
    - README_data_layer_BBK.md  
    - MISSIONS_WIND_SURF_V1.md  
    - schema_rotor.json / schema_pad.json / schema_vehicle.json  
    - html_scraper.py / ingest_pipeline.py / init.sql  
T6. Ne rien modifier.  
T7. Produire un fichier `documentation/M1_setup_log.md` (≤40 lignes) listant :  
    - date/heure,  
    - commandes exécutées,  
    - arborescence finale,  
    - validation présence fichiers.

------------------------------------------------------------
# 7. Deliverables
D1. Arborescence complète `big_brake_kit/`.  
D2. Tous les fichiers rangés à leur emplacement exact.  
D3. Fichiers CSV seed générés.  
D4. Log `documentation/M1_setup_log.md`.  
D5. Aucune ligne de code modifiée.

------------------------------------------------------------
# 8. Logs Obligatoires
Avant validation finale, fournir :
- sortie `ls -R big_brake_kit/`  
- contenu `documentation/M1_setup_log.md`  
- confirmation que Windsurf a bien chargé tous les fichiers en read-only.

------------------------------------------------------------
# 9. Success Criteria
Mission considérée comme terminée lorsque :
- l’arborescence est exacte bit-à-bit,
- tous les fichiers sont présents,
- aucun fichier non autorisé n’a été modifié,
- le log M1 est complet,
- Windsurf a loaded le contexte complet (docs + schémas),
- aucune anomalie structurelle.

------------------------------------------------------------
# END OF WORKFLOW
