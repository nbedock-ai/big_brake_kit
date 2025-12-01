# bbk_mission09_dedup_v1.workflow

## Contexte

Projet : **BigBrakeKit — Déduplication V1 dans l’ingestion**

État actuel :

- **Schémas JSON** stables : `schema_rotor.json`, `schema_pad.json`, `schema_vehicle.json`.
- **Data layer complet** :
  - Rotors : `parse_dba_rotor_page` / `normalize_rotor`.
  - Pads : `parse_ebc_pad_page` / `normalize_pad`.
  - Vehicles : `parse_wheelsize_vehicle_page` / `normalize_vehicle`.
- **Ingestion DB** :
  - `database/ingest_pipeline.py` :
    - `insert_rotor`, `insert_pad`, `insert_vehicle`.
    - `process_rotor_seed`, `process_pad_seed`, `process_vehicle_seed`.
    - `ingest_all(group: str | None = None)`.
- **CLI** :
  - `scrape_and_ingest.py` (Mission 8) wrappe `ingest_all`.

Problème restant : **aucune déduplication**. Relancer `ingest_all()` ou ajouter des seeds qui recoupent des modèles existants duplique les entrées.

Mission 9 : ajouter une **déduplication V1** simple côté DB, sans toucher à la structure des tables.

---

## Règles globales Windsurf / BigBrakeKit

- **Max 100 lignes par bloc de modification.**
- Ne pas modifier l’arborescence du projet.
- Ne pas modifier la signature de `ingest_all` ni celle de `insert_*`.
- Ne pas modifier `scrape_and_ingest.py` (M8 figée).
- Pas de nouvelle dépendance externe (bibliothèque standard uniquement).
- Après modifications, exécuter les tests (`pytest`) et s’assurer qu’ils passent tous.

---

## Étape 1 — Lecture du contexte précis

1. Ouvrir et lire :

   - `database/ingest_pipeline.py`
     - Localiser :
       - `insert_rotor`, `insert_pad`, `insert_vehicle`.
       - `process_rotor_seed`, `process_pad_seed`, `process_vehicle_seed`.
       - `ingest_all`.
   - `database/init.sql`
     - Vérifier l’absence de contraintes `UNIQUE` actuelles sur les tables.
   - `schema_rotor.json`, `schema_pad.json`, `schema_vehicle.json`
     - Confirmer la présence des champs utilisés comme clés de déduplication :
       - Rotors : `brand`, `catalog_ref`.
       - Pads : `shape_id`, `brand`, `catalog_ref`.
       - Vehicles : `make`, `model`, `year_from`.
   - `documentation/README_data_layer_BBK.md`
     - Noter la section actuelle sur `ingest_all` (M7) ; elle sera complétée.

Aucune modification dans cette étape.

---

## Étape 2 — Design de la déduplication V1

Stratégie choisie : **déduplication côté DB**, par requête `SELECT` **avant insertion**.

### 2.1. Clés de déduplication

- **Rotors**
  - Clé : `(brand, catalog_ref)`
- **Pads**
  - Clé : `(shape_id, brand, catalog_ref)`
- **Vehicles**
  - Clé : `(make, model, year_from)`

Ces champs sont **obligatoires** au niveau des schémas JSON, donc toujours présents dans les dicts normalisés.

### 2.2. Où implémenter

Ne pas changer la signature de `insert_*`. On garde `insert_rotor/pad/vehicle` comme **fonctions “brutes”**.

Ajouter :

- de **petits helpers** de type `*_exists` dans `ingest_pipeline.py`, qui interrogent la DB,
- et intégrer ces checks dans les fonctions `process_*_seed`, avant les `insert_*`.

Schéma :

```text
seed → fetch_html → parse_* → normalize_* → dict
    → check_exists(conn, dict)
        - True  → log "duplicate, skip"
        - False → insert_*()
2.3. Scope de la déduplication
Déduplication contre la DB existante (pas seulement en mémoire sur le run courant).

Effet : relancer ingest_all() sur les mêmes seeds ne crée pas de doublons de clés.

Étape 3 — Helpers *_exists (≤100 lignes)
Dans database/ingest_pipeline.py, ajouter en haut ou juste après les insert_* :

Helper rotors :

python
Copy code
def rotor_exists(conn, rotor: dict) -> bool:
    sql = """
    SELECT 1 FROM rotors
    WHERE brand = ? AND catalog_ref = ?
    LIMIT 1
    """
    cur = conn.execute(sql, (rotor.get("brand"), rotor.get("catalog_ref")))
    return cur.fetchone() is not None
Helper pads :

python
Copy code
def pad_exists(conn, pad: dict) -> bool:
    sql = """
    SELECT 1 FROM pads
    WHERE shape_id = ? AND brand = ? AND catalog_ref = ?
    LIMIT 1
    """
    cur = conn.execute(sql, (
        pad.get("shape_id"),
        pad.get("brand"),
        pad.get("catalog_ref"),
    ))
    return cur.fetchone() is not None
Helper vehicles :

python
Copy code
def vehicle_exists(conn, vehicle: dict) -> bool:
    sql = """
    SELECT 1 FROM vehicles
    WHERE make = ? AND model = ? AND year_from = ?
    LIMIT 1
    """
    cur = conn.execute(sql, (
        vehicle.get("make"),
        vehicle.get("model"),
        vehicle.get("year_from"),
    ))
    return cur.fetchone() is not None
Contraintes :

Rester globalement sous 100 lignes pour ce bloc additionnel.

Ne pas modifier insert_rotor, insert_pad, insert_vehicle.

Étape 4 — Intégration dans process_*_seed
Dans les fonctions process_rotor_seed, process_pad_seed, process_vehicle_seed de ingest_pipeline.py :

4.1 Rotors
Dans la boucle sur les dicts normalisés :

Avant insert_rotor(conn, rotor_dict) :

python
Copy code
if rotor_exists(conn, rotor_dict):
    # optionnel : print(f"[ROTOR] Duplicate {brand}/{catalog_ref}, skipping")
    continue
insert_rotor(conn, rotor_dict)
inserted += 1
4.2 Pads
Analogique :

python
Copy code
if pad_exists(conn, pad_dict):
    # print duplicate info
    continue
insert_pad(conn, pad_dict)
inserted += 1
4.3 Vehicles
Analogique :

python
Copy code
if vehicle_exists(conn, vehicle_dict):
    # print duplicate info
    continue
insert_vehicle(conn, vehicle_dict)
inserted += 1
Rappel :

Ne pas casser la logique d’erreur existante (try/except autour des URLs).

Ne pas modifier la signature ni la valeur de retour des process_*_seed (toujours retourner le nombre d’insertions, pas le nombre total d’objets vus).

Étape 5 — Tests de déduplication
Ajouter des tests dans un fichier nouveau ou existant :

Option 1 : nouveau fichier test_dedup_v1.py.

Option 2 : étendre test_ingest_pipeline.py si c’est plus naturel.

5.1. Setup commun
Utiliser une base SQLite en mémoire : sqlite3.connect(":memory:").

Appliquer le schema init.sql dans cette base :

lire le fichier,

conn.executescript(schema_sql).

5.2. Tests à écrire
Rotor double insert (même clé)

Créer un dict rotor valide avec (brand, catalog_ref) donnés.

Appeler insert_rotor(conn, rotor) une fois.

Créer un faux process_rotor_seed minimal (ou directement appeler rotor_exists) pour simuler la logique :

Vérifier que rotor_exists(conn, rotor) retourne True.

S’assurer que la fonction de traitement ne ré-insère pas :

Compter le nombre de lignes dans rotors (SELECT COUNT(*)).

Doit rester à 1 après un second passage.

Pads dédoublonnés

Idem avec un pad (même shape_id, brand, catalog_ref).

Vérifier que la seconde tentative n’ajoute pas de ligne.

Vehicles dédoublonnés

Insérer un véhicule (make="Honda", model="Civic", year_from=2016, ...).

Vérifier qu’un second passage avec les mêmes clés est ignoré.

Important : s’assurer que la logique ne dépend pas de id (AUTO_INCREMENT).

Non-duplicat

Vérifier que deux rotors avec le même brand mais catalog_ref différent sont tous deux insérés (COUNT=2).

Idem pour pads et vehicles via leurs clés respectives.

Intégration ingest_all (facultatif mais souhaitable)

Monkeypatcher fetch_html + parsers pour retourner de petites listes contenant des doublons (même clé).

Lancer ingest_all(group="vehicles") sur une DB mémoire.

Vérifier que le nombre de lignes insérées correspond au nombre de clés uniques, pas au nombre total d’objets retournés.

Exécuter :

bash
Copy code
pytest -q
Tous les tests (anciens + nouveaux) doivent être verts.

Étape 6 — Documentation & Log M9
README_data_layer_BBK.md

Ajouter une sous-section dans la partie ingestion (4.x), par exemple :

4.x Déduplication V1 (ingest_all)

Contenu minimal :

Explication des clés :

Rotors : (brand, catalog_ref).

Pads : (shape_id, brand, catalog_ref).

Vehicles : (make, model, year_from).

Comportement :

si une entrée avec la clé existe déjà en base, elle est ignorée au run suivant.

pas de déduplication “floue” ni cross-type.

Impact :

ingest_all devient idempotent (sur les mêmes seeds).

Log de mission

Créer documentation/M9_dedup_v1_log.md avec :

Objectif de M9.

Design choisi (helpers *_exists, intégration dans process_*_seed).

Clés de déduplication utilisées.

Résumé des tests (liste des cas).

Limites connues (pas de clustering, pas de merge, etc.).

Étape 7 — Git
Vérifier l’état :

bash
Copy code
git status
Committer :

Message recommandé :

bash
Copy code
git commit -am "Mission 9: add naive deduplication in ingest pipeline"
Pousser :

bash
Copy code
git push
Critères de complétion Mission 9
Mission 9 est terminée lorsque :

database/ingest_pipeline.py contient des helpers de déduplication et les utilise dans process_rotor_seed, process_pad_seed, process_vehicle_seed.

Le pipeline ingest_all() ne crée plus de doublons sur (brand, catalog_ref) / (shape_id, brand, catalog_ref) / (make, model, year_from) lors des relances.

Un jeu de tests couvre ces cas (rotors, pads, vehicles) et tous les tests du projet passent.

README_data_layer_BBK.md documente clairement les règles de Déduplication V1.

documentation/M9_dedup_v1_log.md existe et décrit l’implémentation.

Les changements sont committés et poussés sur le dépôt BigBrakeKit.