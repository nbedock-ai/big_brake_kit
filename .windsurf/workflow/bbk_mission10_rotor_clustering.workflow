# bbk_mission10_rotor_clustering.workflow

## Contexte

Projet : **BigBrakeKit — Analyse préliminaire des rotors**

Missions déjà terminées (V1 data layer) :

- M2–M3 : rotors (parse + normalize) → `schema_rotor.json`.
- M4 : pads.
- M5–M6 : véhicules.
- M7 : `ingest_all()` vers SQLite `database/bbk.db`.
- M8 : CLI `scrape_and_ingest.py`.
- M9 : déduplication V1 (pipeline idempotent).

La table `rotors` est remplie avec des lignes conformes à `schema_rotor.json`.

Mission 10 : **analyser les rotors existants** dans la DB et produire une première segmentation géométrique, qui servira de base à M11 pour choisir 15–25 rotors maîtres.

---

## Règles globales Windsurf / BigBrakeKit

- **Max 100 lignes de code par bloc d’édition.**
- Ne pas modifier les modules déjà stabilisés (scraping, normalisation, ingestion, CLI, dédup V1).
- Ne pas changer le schéma SQL (`database/init.sql`) ni `schema_rotor.json`.
- Utiliser uniquement la bibliothèque standard Python (pas de pandas, pas de numpy, pas de scikit-learn).
- Après modifications : exécuter les tests (`pytest`) et s’assurer qu’ils passent tous.

---

## Étape 1 — Lecture du contexte

1. Ouvrir et lire :

   - `schema_rotor.json` :
     - repérer les champs :
       - `outer_diameter_mm`
       - `nominal_thickness_mm`
       - `hat_height_mm`
       - `overall_height_mm`
       - `offset_mm` (optionnel)
       - `brand`
       - `catalog_ref`
   - `database/init.sql` :
     - structure de la table `rotors` (noms des colonnes).
   - `database/ingest_pipeline.py` :
     - pour voir comment les rotors sont insérés et sous quels noms de colonnes.
   - `documentation/README_data_layer_BBK.md` :
     - sections décrivant les rotors et l’usage “clustering / rotors maîtres”.
   - `DocDeTravail_BigBrakeKit.md` :
     - sections sur la banque de rotors maîtres et leur rôle.

2. Vérifier :

   - que les champs géométriques nécessaires sont bien présents en base (`rotors`),
   - que `bbk.db` est le chemin canonique pour la DB.

Aucune modification de code dans cette étape.

---

## Étape 2 — Création du module `rotor_analysis/clustering.py`

1. Créer le répertoire (si absent) :

   - `rotor_analysis/`

2. Créer le fichier :

   - `rotor_analysis/clustering.py`

3. Contenu attendu (structure générale, sans tout coder en une fois) :

   - Imports :
     - `sqlite3`
     - `json`
     - `dataclasses` (facultatif mais recommandé pour structurer les clusters)
     - `math`
     - `typing` (`List`, `Dict`, `Optional`)

   - Constantes :

     ```python
     DB_PATH = "database/bbk.db"

     DIAM_BIN_STEP_MM = 5.0
     THICK_BIN_STEP_MM = 0.5
     OFFSET_BIN_STEP_MM = 2.0
     ```

   - Fonctions principales à définir :

     - `load_rotors_from_db(db_path: str = DB_PATH) -> list[dict]`
     - `effective_offset_mm(rotor: dict) -> Optional[float]`
     - `compute_cluster_key(rotor: dict) -> Optional[tuple[float, float, float]]`
     - `build_clusters(rotors: list[dict]) -> dict`
       - retourne une structure interne `{key: {"members": [...], "stats": {...}}}`
     - `clusters_to_json_serializable(clusters: dict) -> dict`
       - convertit les keys tuple en objets pour JSON.
     - `run_clustering(db_path: str = DB_PATH, output_path: str = "rotor_analysis/rotor_clusters.json") -> None`

   - Optionnel : un petit `if __name__ == "__main__": run_clustering()` pour exécution directe.

---

## Étape 3 — Implémentation des helpers de données (≤100 lignes)

Dans `rotor_analysis/clustering.py` :

1. `load_rotors_from_db` :

   - Ouvrir une connexion SQLite sur `db_path`.
   - `SELECT` sur la table `rotors` pour extraire au minimum les colonnes :
     - `outer_diameter_mm`
     - `nominal_thickness_mm`
     - `hat_height_mm`
     - `overall_height_mm`
     - `offset_mm`
     - `brand`
     - `catalog_ref`
   - Retourner une liste de dicts Python (clé=nom de colonne).

2. `effective_offset_mm` :

   - Inputs : dict `rotor`.
   - Logique :
     - si `offset_mm` est non null → le retourner (float).
     - sinon, si `overall_height_mm` et `hat_height_mm` sont non null :
       - `offset = overall_height_mm - hat_height_mm`
       - retourner `offset`.
     - sinon :
       - retourner `None`.

3. Gestion minimale des erreurs :

   - Skipper les rotors avec valeurs manifestement invalides (ex : `outer_diameter_mm` ou `nominal_thickness_mm` null).

---

## Étape 4 — Définition du schéma de clustering

1. `compute_cluster_key(rotor: dict) -> Optional[tuple[float, float, float]]` :

   - Extraire :
     - `outer_diameter_mm`
     - `nominal_thickness_mm`
     - `offset_eff = effective_offset_mm(rotor)`
   - Si l’un est `None` → retourner `None` (rotor ignoré).
   - Calculer les bins :

     ```python
     def bin_value(x: float, step: float) -> float:
         return round(x / step) * step
     ```

     - `diam_bin = bin_value(outer_diameter_mm, DIAM_BIN_STEP_MM)`
     - `thick_bin = bin_value(nominal_thickness_mm, THICK_BIN_STEP_MM)`
     - `offset_bin = bin_value(offset_eff, OFFSET_BIN_STEP_MM)`

   - Retourner `(diam_bin, thick_bin, offset_bin)`.

2. Commentaire dans le code pour documenter que c’est un **clustering préliminaire par binning**, non un vrai k-means.

---

## Étape 5 — Construction des clusters

Implémenter `build_clusters(rotors: list[dict]) -> dict` :

1. Initialiser un dict vide `clusters = {}`.

2. Pour chaque rotor :

   - `key = compute_cluster_key(rotor)`
   - si `key is None` → ignorer.
   - sinon :
     - si `key` pas encore dans `clusters`, initialiser :

       ```python
       clusters[key] = {
           "members": [],
           "sum_diameter": 0.0,
           "sum_thickness": 0.0,
           "sum_offset": 0.0,
           "count": 0,
       }
       ```

     - Ajouter le rotor à `members` avec les champs utiles :
       - au minimum : `brand`, `catalog_ref`, `outer_diameter_mm`, `nominal_thickness_mm`, `offset_eff`.
     - Mettre à jour les sommes et `count`.

3. Après la boucle :

   - pour chaque cluster :
     - calculer les centroides :

       ```python
       centroid = {
           "outer_diameter_mm": cluster["sum_diameter"] / cluster["count"],
           "nominal_thickness_mm": cluster["sum_thickness"] / cluster["count"],
           "offset_mm": cluster["sum_offset"] / cluster["count"],
       }
       ```

     - stocker dans `cluster["centroid"]`.
     - éventuellement supprimer les clés `sum_*` (non nécessaires pour JSON final).

4. Retourner `clusters`.

---

## Étape 6 — Sérialisation JSON

Implémenter `clusters_to_json_serializable(clusters: dict) -> dict` :

1. Construire un dict :

   ```python
   output = {
       "meta": {
           "diam_bin_step_mm": DIAM_BIN_STEP_MM,
           "thick_bin_step_mm": THICK_BIN_STEP_MM,
           "offset_bin_step_mm": OFFSET_BIN_STEP_MM,
           "cluster_count": len(clusters),
       },
       "clusters": [],
   }
Pour chaque key = (diam_bin, thick_bin, offset_bin) et cluster :

Créer un objet :

python
Copy code
{
    "cluster_id": idx,  # indice séquentiel
    "key": {
        "outer_diameter_mm": diam_bin,
        "nominal_thickness_mm": thick_bin,
        "offset_mm": offset_bin,
    },
    "centroid": cluster["centroid"],
    "count": cluster["count"],
    "members": cluster["members"],
}
Ajouter à output["clusters"].

Retourner output.

Étape 7 — Fonction run_clustering + écriture fichier
Implémenter run_clustering(db_path=DB_PATH, output_path="rotor_analysis/rotor_clusters.json") :

Charger les rotors : rotors = load_rotors_from_db(db_path).

Construire les clusters : clusters = build_clusters(rotors).

Transformer pour JSON : data = clusters_to_json_serializable(clusters).

Créer le répertoire rotor_analysis/ s’il n’existe pas.

Écrire le fichier :

python
Copy code
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
Optionnel : print d’un petit récapitulatif (nombre de rotors, clusters, etc.).

Ajouter :

python
Copy code
if __name__ == "__main__":
    run_clustering()
Étape 8 — Tests unitaires
Créer test_rotor_clustering.py à la racine du projet (même niveau que les autres tests).

8.1. Tests de binning
Tester compute_cluster_key sur quelques cas simples :

rotor A : outer_diameter_mm=280, nominal_thickness_mm=22.4, offset_mm=45
→ vérifier les bins attendus (avec les steps définis).

rotor B : offset_mm=None, overall_height_mm=50, hat_height_mm=10
→ offset_eff=40, bin correct.

rotor incomplet (outer_diameter_mm=None) → retourne None.

8.2. Tests de clustering
Construire une petite liste de 4–6 rotors synthétiques :

deux rotors très proches → même cluster key,

un rotor plus loin → autre cluster key.

Appeler build_clusters(rotors) :

vérifier :

nombre de clusters attendu,

count correct par cluster,

centroides corrects (moyenne naïve).

members contient brand + catalog_ref.

8.3. Tests de sérialisation
Appeler clusters_to_json_serializable sur un dict de clusters minimal :

vérifier la structure globale (meta, clusters),

cluster_id séquentiels,

key et centroid présents,

count correct.

Exécuter :

bash
Copy code
pytest test_rotor_clustering.py
S’assurer que tous les tests passent et qu’aucun test existant n’est cassé.

Étape 9 — Documentation & log
README_data_layer_BBK.md

Ajouter une section dédiée aux analyses rotors, par exemple :

5.1 Analyse préliminaire des rotors (M10)

Contenu :

But : segmenter l’espace des rotors en familles géométriques.

Fichier : rotor_analysis/clustering.py.

Features utilisées : outer_diameter_mm, nominal_thickness_mm, offset_mm (ou fallback).

Méthode : clustering par binning (pas de k-means pour V1).

Output : rotor_analysis/rotor_clusters.json.

Lien direct avec M11 : sélection de rotors maîtres dans chaque cluster.

Log de mission M10

Créer documentation/M10_rotor_clustering_log.md :

Objectif mission.

Description de l’algorithme de binning.

Détails sur les pas de bins choisis (5 / 0.5 / 2 mm) et justification.

Résumé des tests.

Limitations V1 (ex : pas de pondération par disponibilité, pas de clustering avancé).

Pistes d’extension (V2 : k-means, pondération, utilisation de rotor_weight_kg, etc.).

Étape 10 — Git
Vérifier :

bash
Copy code
git status
Commit :

bash
Copy code
git commit -am "Mission 10: preliminary rotor clustering (geometry binning)"
Push :

bash
Copy code
git push
Critères de complétion de Mission 10
Mission 10 est terminée lorsque :

rotor_analysis/clustering.py existe et expose au minimum :

load_rotors_from_db,

effective_offset_mm,

compute_cluster_key,

build_clusters,

clusters_to_json_serializable,

run_clustering.

rotor_analysis/rotor_clusters.json peut être généré à partir d’une DB peuplée.

test_rotor_clustering.py existe, tous ses tests passent, et les tests existants restent verts.

README_data_layer_BBK.md décrit clairement l’analyse M10.

documentation/M10_rotor_clustering_log.md résume l’implémentation.

Les changements sont committés et poussés sur le dépôt BigBrakeKit.