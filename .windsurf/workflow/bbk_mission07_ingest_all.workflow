# bbk_mission07_ingest_all.workflow

## Contexte

Projet : **BigBrakeKit — couche ingestion base de données**

Tu exécutes **Mission 7 : Implémenter `ingest_all()`**.

État actuel :

- Schémas JSON figés : `schema_rotor.json`, `schema_pad.json`, `schema_vehicle.json`.
- DB et tables définies dans : `database/init.sql`.
- Scrapers + normalizers opérationnels :
  - `parse_dba_rotor_page` / `normalize_rotor`
  - `parse_ebc_pad_page` / `normalize_pad`
  - `parse_wheelsize_vehicle_page` / `normalize_vehicle`
- Fichier d’ingestion existant mais minimal :
  - `database/ingest_pipeline.py` (helpers `insert_rotor`, `insert_pad`, `insert_vehicle`, `ingest_jsonl`).
- Seeds d’URL définis dans :
  - `data_seed_url.txt`
  - `data_scraper/exporters/urls_seed_rotors.csv`
  - `data_scraper/exporters/urls_seed_pads.csv`
  - `data_scraper/exporters/urls_seed_vehicles.csv`

Mission 7 doit fournir **un point d’entrée unique** `ingest_all()` qui lit les seeds, appelle les scrapers/normalizers, puis insère dans la DB SQLite.

---

## Règles globales Windsurf / BigBrakeKit

- **Max 100 lignes de code par bloc d’édition.**
- Ne pas modifier l’arborescence du projet.
- Ne pas casser les fonctions existantes (`insert_*`, `ingest_jsonl`).
- Exécuter les tests ou scripts de vérification après modifications critiques.
- Préserver la compatibilité avec M2–M6 (rotors, pads, véhicules déjà stables).

---

## Étape 1 — Lecture du contexte technique

1. Ouvrir et lire :

   - `database/ingest_pipeline.py`
   - `data_scraper/html_scraper.py`
   - `database/init.sql`
   - `data_seed_url.txt`
   - `data_scraper/exporters/urls_seed_rotors.csv`
   - `data_scraper/exporters/urls_seed_pads.csv`
   - `data_scraper/exporters/urls_seed_vehicles.csv`
   - `documentation/README_data_layer_BBK.md`
   - `MISSIONS_WIND_SURF_V1.md` (section **M7 — Implémenter pipeline ingest_all()**)

2. Vérifier :

   - Les signatures de :
     - `fetch_html`
     - `parse_dba_rotor_page`, `normalize_rotor`
     - `parse_ebc_pad_page`, `normalize_pad`
     - `parse_wheelsize_vehicle_page`, `normalize_vehicle`
   - La structure des tables `rotors`, `pads`, `vehicles` dans `init.sql`.

Aucune modification de code dans cette étape.

---

## Étape 2 — Design du pipeline `ingest_all()`

Objectif : définir la structure avant d’écrire du code.

1. API cible :

   ```python
   def ingest_all() -> None:
       ...
Optionnellement, un paramètre group: str | None pour filtrer sur "rotors", "pads", "vehicles", mais la spec M7 impose au minimum une fonction sans argument qui traite les trois.

Structure logique :

Phase 1 : lire les seeds.

Phase 2 : ouvrir la connexion SQLite.

Phase 3 : pour chaque groupe :

itérer sur les URLs,

scraper + normaliser,

filtrer,

insérer.

Découpage en helpers :

load_seed_csv_paths() : lire data_seed_url.txt et retourner un dict { "rotors": [path_csv], "pads": [...], "vehicles": [...] }.

Pour la version actuelle du repo : prendre toutes les lignes qui contiennent "urls_seed_" et un suffixe "_rotors.csv", "_pads.csv", "_vehicles.csv".

iter_seed_urls(kind: str) :

ouvrir les CSV correspondants,

produire des tuples (source, url, notes).

process_rotor_seed(conn, source: str, url: str) :

html = fetch_html(url)

raw_list = parse_dba_rotor_page(html, source=source) (adapter à la signature réelle)

norm_list = [normalize_rotor(raw, source=source) ...]

filtrer et insérer avec insert_rotor.

process_pad_seed(conn, source: str, url: str) :

idem avec parse_ebc_pad_page / normalize_pad / insert_pad.

process_vehicle_seed(conn, source: str, url: str) :

idem avec parse_wheelsize_vehicle_page / normalize_vehicle / insert_vehicle.

Filtre minimal avant insertion :

catcher les exceptions de parsing/normalisation par URL :

log simple (print ou logger minimal) et continue.

ne pas insérer :

objets None,

dicts vides,

dicts où les champs requis (par schéma) sont manifestement absents.

la déduplication “intelligente” sera traitée en M9 ; ici uniquement un filtre de sanité.

Étape 3 — Helpers de lecture des seeds (≤100 lignes)
Dans database/ingest_pipeline.py, ajouter :

load_seed_csv_paths() :

ouvrir data_seed_url.txt,

pour chaque ligne contenant .csv :

déduire le groupe :

*rotors.csv → "rotors"

*pads.csv → "pads"

*vehicles.csv → "vehicles"

ajouter le chemin à une liste dans dict[group].

iter_seed_urls(kind: str) :

pour chaque CSV dans paths[kind] :

ouvrir en utf-8,

sauter la ligne d’en-tête si présente,

yield (source, url, notes) pour chaque ligne non vide.

Respecter :

pas de dépendance externe (uniquement csv standard lib).

garder ce bloc sous 100 lignes.

Étape 4 — Helpers de traitement par groupe
Ajouter dans database/ingest_pipeline.py :

process_rotor_seed(conn, source: str, url: str) -> int :

html = fetch_html(url)

récupérer la liste des rotors bruts via parse_dba_rotor_page.

normaliser avec normalize_rotor.

filtrer les résultats invalides.

appeler insert_rotor pour chaque dict valide.

retourner le nombre de lignes insérées.

process_pad_seed(conn, source: str, url: str) -> int :

idem avec parse_ebc_pad_page et normalize_pad puis insert_pad.

process_vehicle_seed(conn, source: str, url: str) -> int :

raw_list = parse_wheelsize_vehicle_page(html)

pour chaque raw :

norm = normalize_vehicle(raw, source="wheelsize")

filtrer les cas invalides

insert_vehicle(conn, norm)

retourner le nombre de lignes insérées.

Gestion des erreurs :

try/except autour de chaque URL :

en cas d’erreur réseau ou parsing : logguer et retourner 0.

ne jamais laisser une exception interrompre ingest_all().

Étape 5 — Implémentation de ingest_all()
Implémenter :

python
Copy code
def ingest_all(group: str | None = None) -> None:
    """
    Si group est None: traite rotors, pads, vehicles.
    Sinon: group ∈ {"rotors", "pads", "vehicles"}.
    """
    ...
Logique :

paths = load_seed_csv_paths()

conn = sqlite3.connect(DB_PATH)

pour chacun des groupes ["rotors", "pads", "vehicles"] :

si group est fourni et différent → skip.

pour chaque (source, url, notes) de iter_seed_urls(kind) :

appeler process_*_seed.

accumuler un compteur global d’insertions.

commit à la fin.

fermer la connexion.

Ajouter un petit CLI minimal (optionnel mais utile) :

python
Copy code
if __name__ == "__main__":
    ingest_all()
pour pouvoir lancer python -m database.ingest_pipeline depuis la racine du projet.

Étape 6 — Vérifications / Tests
Ajouter un test léger (sans réseau) dans un nouveau fichier test_ingest_pipeline.py :

utiliser sqlite3.connect(":memory:") ou une DB temporaire,

monkeypatcher :

fetch_html pour retourner du HTML factice,

parse_* / normalize_* pour retourner 1–2 objets simples,

tester que :

process_rotor_seed / process_pad_seed / process_vehicle_seed insèrent bien dans la table correspondante,

ingest_all(group="rotors") appelle uniquement le pipeline rotors.

Lancer au minimum :

pytest test_ingest_pipeline.py

et vérifier qu’aucun test existant n’est cassé.

Étape 7 — Documentation & Log de mission
Mettre à jour documentation/README_data_layer_BBK.md :

ajouter une courte section décrivant le pipeline :

urls_seed_*.csv → ingest_all() → DB bbk.db.

préciser la relation avec les Missions M2–M6.

Créer documentation/M7_ingest_all_log.md :

résumer :

design de ingest_all,

format attendu des seeds,

gestion des erreurs,

limites connues (pas encore de déduplication avancée).

Étape 8 — Git
Vérifier l’état :

git status

Commit :

git commit -am "Mission 7: implement ingest_all pipeline (rotors/pads/vehicles)"

Push :

git push

Critères de complétion de Mission 7
Mission 7 est terminée lorsque :

database/ingest_pipeline.py expose un ingest_all() opérationnel.

Les helpers de lecture des seeds et de traitement par groupe sont en place.

Un test minimal test_ingest_pipeline.py existe et passe.

README_data_layer_BBK.md documente le pipeline d’ingestion.

M7_ingest_all_log.md décrit l’implémentation.

Le tout est committé et poussé sur le dépôt BigBrakeKit.

Copy code
