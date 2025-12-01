# bbk_mission08_scrape_and_ingest.workflow

## Contexte

Projet : **BigBrakeKit — couche ingestion / CLI**

Tu exécutes **Mission 8 : Script CLI `scrape_and_ingest.py`**.

État actuel :

- `database/ingest_pipeline.py` :
  - `ingest_all(group: str | None = None)` opérationnel (M7).
- Data layer complet :
  - rotors / pads / vehicles → scrapers + normalizers + ingestion DB.
- Seeds CSV définis et utilisés par `ingest_all`.

Mission 8 doit fournir un **script à la racine** du dépôt :

- `scrape_and_ingest.py`  
- CLI simple pour piloter `ingest_all` depuis le shell.

---

## Règles globales Windsurf / BigBrakeKit

- **Max 100 lignes de code par bloc d’édition.**
- Utiliser uniquement la bibliothèque standard Python (`argparse`, `sys`).
- Ne rien modifier dans `database/ingest_pipeline.py` (M7 est figée).
- Toujours exécuter les tests après modifications.
- Pas de refonte d’arborescence.

---

## Étape 1 — Lecture du contexte

1. Ouvrir et lire :

   - `database/ingest_pipeline.py`
   - `documentation/README_data_layer_BBK.md`
   - `MISSIONS_WIND_SURF_V1.md` (section **M8 — Script CLI scrape_and_ingest.py**)

2. Vérifier :

   - Signature exacte de `ingest_all`.
   - Comment les groupes sont nommés (`"rotors"`, `"pads"`, `"vehicles"`).
   - Comment la doc actuelle parle de l’ingestion (section 4).

Aucune modification dans cette étape.

---

## Étape 2 — Design de la CLI

Spécification CLI :

- Script : `scrape_and_ingest.py` à la **racine** du projet.
- Interface :

  ```bash
  # Par défaut : tout ingérer
  python scrape_and_ingest.py

  # Sélection explicite
  python scrape_and_ingest.py --only all
  python scrape_and_ingest.py --only rotors
  python scrape_and_ingest.py --only pads
  python scrape_and_ingest.py --only vehicles
Implémentation :

Utiliser argparse.ArgumentParser.

Argument :

--only avec choices=["all", "rotors", "pads", "vehicles"], défaut "all".

Mapping vers ingest_all :

"all" → ingest_all()

"rotors" → ingest_all("rotors")

"pads" → ingest_all("pads")

"vehicles" → ingest_all("vehicles")

Structure :

python
Copy code
import argparse
from database.ingest_pipeline import ingest_all

def main(argv: list[str] | None = None) -> None:
    ...

if __name__ == "__main__":
    main()
Le paramètre argv permet les tests unitaires (appel main([...]) sans passer par sys.argv).

Étape 3 — Création de scrape_and_ingest.py (≤100 lignes)
Créer le fichier à la racine du repo :

scrape_and_ingest.py

Contenu à implémenter :

Imports :

argparse

sys (optionnel si tu veux passer sys.argv[1:] à main)

ingest_all depuis database.ingest_pipeline.

Fonction parse_args(argv) interne qui construit le parser et renvoie Namespace.

Fonction main(argv: list[str] | None = None) :

Récupérer args = parse_args(argv).

Log léger sur la cible (ex. print d’un header optionnel).

Router vers ingest_all selon args.only.

Contraintes :

Un seul fichier, un seul point d’entrée.

Garde tout le fichier bien en dessous de 100 lignes.

Exécution manuelle attendue après implémentation :

bash
Copy code
python scrape_and_ingest.py --only vehicles
python scrape_and_ingest.py --only rotors
python scrape_and_ingest.py --only pads
python scrape_and_ingest.py --only all
python scrape_and_ingest.py              # même effet que --only all
Étape 4 — Tests unitaires CLI
Créer un fichier de tests :

test_scrape_and_ingest_cli.py à la racine des tests (même niveau que test_ingest_pipeline.py).

Stratégie de test : sans toucher à la vraie DB ni aux vraies seeds.

Importer scrape_and_ingest.

Monkeypatcher database.ingest_pipeline.ingest_all pour :

enregistrer les appels,

ne rien faire côté DB.

Tester les cas :

Sans argument :

Appeler scrape_and_ingest.main([]).

Vérifier que ingest_all est appelée une fois avec group=None.

--only all :

main(["--only", "all"]) → ingest_all(group=None).

--only rotors :

main(["--only", "rotors"]) → ingest_all("rotors").

--only pads :

main(["--only", "pads"]) → ingest_all("pads").

--only vehicles :

main(["--only", "vehicles"]) → ingest_all("vehicles").

Exécuter les tests :

pytest test_scrape_and_ingest_cli.py

S’assurer que tous les tests existants passent encore.

Étape 5 — Mise à jour documentation
Modifier documentation/README_data_layer_BBK.md :

Dans la section ingestion (4.x, déjà créée en M7) :

Ajouter un sous-paragraphe “4.x CLI scrape_and_ingest.py” décrivant :

le script,

la syntaxe :

bash
Copy code
python scrape_and_ingest.py --only all|rotors|pads|vehicles
la valeur par défaut (all quand aucun --only n’est donné).

Ne rien changer aux descriptions M2–M7, uniquement compléter la partie CLI.

Étape 6 — Log de mission M8
Créer documentation/M8_scrape_and_ingest_log.md avec :

Objectif de M8.

Description de l’interface CLI (arguments, mapping vers ingest_all).

Résumé des tests unitaires (ce qui est vérifié).

Limites connues (pas de logging avancé, pas de config fichier, etc.).

Étape 7 — Git
Vérifier l’état :

git status

Committer :

Message recommandé :

"Mission 8: add scrape_and_ingest CLI wrapper for ingest_all"

Pousser :

git push

Critères de complétion de Mission 8
Mission 8 est terminée lorsque :

Le fichier scrape_and_ingest.py existe à la racine et :

peut être exécuté avec python scrape_and_ingest.py ...,

route correctement vers ingest_all selon --only.

test_scrape_and_ingest_cli.py existe et tous les tests passent.

README_data_layer_BBK.md documente clairement l’usage du script CLI.

documentation/M8_scrape_and_ingest_log.md est créé.

Le tout est committé et poussé sur le dépôt BigBrakeKit.