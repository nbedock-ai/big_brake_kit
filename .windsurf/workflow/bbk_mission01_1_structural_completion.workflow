bbk_mission01_1_structural_completion.workflow
# BigBrakeKit — Mission 1.1
# Structural Completion: Hydraulics + Bracket Geometry + Fittings + Caliper Hydraulic Config
# Status: Pending

------------------------------------------------------------
# 0. Mission Identifier
Compléter la structure du projet BigBrakeKit en ajoutant toutes les couches fonctionnelles manquantes :  
- hydraulics  
- bracket_geometry  
- fittings  
- caliper hydraulic configuration  
+ mise à jour de la documentation.

------------------------------------------------------------
# 1. Scope (strict)
Mission de structure uniquement.  
Aucune logique métier.  
Aucune modification du scraping.  
Aucune modification des schémas JSON V1 existants.  
Tous les nouveaux fichiers sont créés vides mais structurés.  
Les documents sont mis à jour pour refléter la structure complète du projet.

------------------------------------------------------------
# 2. Fichiers (write)
## Nouveaux répertoires
- hydraulics/
- bracket_geometry/
- fittings/

## Fichiers à générer
- hydraulics/segments.json
- hydraulics/vehicle_segment_map.json
- hydraulics/README_hydraulics.md

- bracket_geometry/schema_bracket_geometry.json
- bracket_geometry/README_bracket_geometry.md
- bracket_geometry/normalize_bracket_geometry.py

- caliper_design/hydraulic_config.json

- fittings/catalog.json
- fittings/README_fittings.md

## Documentation à modifier
- documentation/DocDeTravail_BigBrakeKit.md
- documentation/README_data_layer_BBK.md

## Log mission
- documentation/M1_1_structural_completion_log.md

------------------------------------------------------------
# 3. Fichiers (read-only)
- documentation/MISSIONS_WIND_SURF_V1.md
- documentation/DocDeTravail_BigBrakeKit.md (lecture avant écriture)
- documentation/README_data_layer_BBK.md (lecture avant écriture)

------------------------------------------------------------
# 4. Tasks (séquentiel)
T1. Créer les répertoires manquants :  


hydraulics/
bracket_geometry/
fittings/


T2. Générer les fichiers hydraulics :
- `segments.json`  
- `vehicle_segment_map.json`  
- `README_hydraulics.md`

T3. Générer les fichiers bracket geometry :
- `schema_bracket_geometry.json`  
- `README_bracket_geometry.md`  
- `normalize_bracket_geometry.py`

T4. Générer la configuration hydraulique des étriers :
- `caliper_design/hydraulic_config.json`

T5. Générer les fichiers fittings :
- `catalog.json`  
- `README_fittings.md`

T6. Modifier `DocDeTravail_BigBrakeKit.md` :
- ajouter section “Structure Complète V1+Hydraulics”
- ajouter sous-sections : hydraulique / geometry / fittings

T7. Modifier `README_data_layer_BBK.md` :
- ajouter “Sources de données additionnelles : hydraulique, bracket_geometry, fittings”
- ajouter références aux nouveaux fichiers

T8. Générer log `M1_1_structural_completion_log.md`

T9. Git add + commit + push

------------------------------------------------------------
# 5. Tests
- Vérifier existence de tous les nouveaux répertoires.
- Vérifier que tous les JSON sont valides via `json.loads`.
- Vérifier que normalize_bracket_geometry.py s’importe sans erreur.
- Vérifier que la documentation contient les nouvelles sections.

------------------------------------------------------------
# 6. Deliverables
- Structure complète pour toutes missions futures M2–M16.
- Couche hydraulique prête pour extension M16.
- Couche bracket geometry prête pour parsing/normalisation.
- Catalogue fittings prêt.
- Documentation mise à jour.
- Log créé.
- Commit + push GitHub.

------------------------------------------------------------
# 7. Fichiers à générer (contenu exact)

## hydraulics/segments.json
```json
{
  "S": { "surface_min_mm2": 0, "surface_max_mm2": null },
  "M": { "surface_min_mm2": null, "surface_max_mm2": null },
  "L": { "surface_min_mm2": null, "surface_max_mm2": null }
}

hydraulics/vehicle_segment_map.json
{}

hydraulics/README_hydraulics.md
# Hydraulics Layer (V2)
Objectif : classifier chaque véhicule dans un segment hydraulique S/M/L.

Variable pertinente : surface totale des pistons de l'étrier (mm²).
Aucune donnée de pression, aucune donnée de diamètre de durite.

Fichiers :
- segments.json : définition des plages S/M/L.
- vehicle_segment_map.json : mapping véhicule → segment hydraulique.

bracket_geometry/schema_bracket_geometry.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "BracketGeometry",
  "type": "object",
  "properties": {
    "knuckle_bolt_spacing_mm": { "type": ["number", "null"] },
    "knuckle_bolt_orientation_deg": { "type": ["number", "null"] },
    "rotor_center_offset_mm": { "type": ["number", "null"] },
    "wheel_inner_barrel_clearance_mm": { "type": ["number", "null"] },
    "max_rotor_diameter_mm": { "type": ["number", "null"] },
    "rotor_thickness_min_mm": { "type": ["number", "null"] },
    "rotor_thickness_max_mm": { "type": ["number", "null"] },
    "is_axial_mount": { "type": ["boolean", "null"] },
    "is_radial_mount": { "type": ["boolean", "null"] },
    "caliper_clearance_mm": { "type": ["number", "null"] }
  },
  "additionalProperties": false
}

bracket_geometry/README_bracket_geometry.md
# Bracket Geometry Layer

Objectif : définir les variables nécessaires pour générer un bracket CNC correct.

Variables :
- knuckle bolt spacing (mm)
- knuckle orientation (deg)
- rotor center offset (mm)
- wheel inner barrel clearance (mm)
- max rotor diameter possible (mm)
- rotor thickness min/max
- axial/radial mount
- caliper clearance

Source : scraping, vision ou valeurs dérivées.

bracket_geometry/normalize_bracket_geometry.py
def normalize_bracket_geometry(raw: dict) -> dict:
    return {
        "knuckle_bolt_spacing_mm": raw.get("knuckle_bolt_spacing_mm"),
        "knuckle_bolt_orientation_deg": raw.get("knuckle_bolt_orientation_deg"),
        "rotor_center_offset_mm": raw.get("rotor_center_offset_mm"),
        "wheel_inner_barrel_clearance_mm": raw.get("wheel_inner_barrel_clearance_mm"),
        "max_rotor_diameter_mm": raw.get("max_rotor_diameter_mm"),
        "rotor_thickness_min_mm": raw.get("rotor_thickness_min_mm"),
        "rotor_thickness_max_mm": raw.get("rotor_thickness_max_mm"),
        "is_axial_mount": raw.get("is_axial_mount"),
        "is_radial_mount": raw.get("is_radial_mount"),
        "caliper_clearance_mm": raw.get("caliper_clearance_mm")
    }

caliper_design/hydraulic_config.json
{
  "2P": { "piston_area_mm2": [] },
  "4P": {
    "S": [],
    "M": [],
    "L": []
  },
  "6P": {
    "S": [],
    "M": [],
    "L": []
  }
}

fittings/catalog.json
{
  "banjo_fittings": [
    "M10x1",
    "M10x1.25",
    "M12x1",
    "inverted_flare"
  ]
}

fittings/README_fittings.md
# Brake Line Fittings (V2)

Standards fournis :
- M10x1 banjo
- M10x1.25 banjo
- M12x1 banjo
- inverted flare

Les fittings ne dépendent pas du véhicule.

8. Documentation: modifications textuelles

Windsurf doit ajouter :

➤ Dans DocDeTravail_BigBrakeKit.md :

Section nouvelle :

1.x — Couche Hydraulique, Bracket Geometry et Fittings

(Suivi d’un résumé des trois couches)

➤ Dans README_data_layer_BBK.md :

Section nouvelle :

7. Données additionnelles

(Description de hydraulics/, bracket_geometry/, fittings/)

END