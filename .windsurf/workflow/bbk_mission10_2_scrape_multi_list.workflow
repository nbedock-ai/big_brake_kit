# bbk_mission10_2_scrape_multi_list.workflow

## Mission 10.2 — Scraping multi-list (catalogues rotors)

### Objectif

Exploiter les URLs de type "catalogue" ajoutées en Mission 10.1 pour :
- extraire automatiquement **plusieurs rotors par page**,
- alimenter le pipeline existant (M2–M3–M7–M9),
- sans modifier la structure globale du data layer.

Cible : passer de quelques dizaines de rotors (≈47) à **plusieurs centaines** en exploitant
2–3 sites bien structurés (tables ou cartes produits HTML statiques).

---

## Contexte et contraintes

- Data layer actuel :
  - `parse_dba_rotor_page` + `normalize_rotor` (M2–M3)
  - `ingest_all` + dédup (M7–M9)
  - clustering (M10)
- Mission 10.1 :
  - `urls_seed_rotors.csv` contient 28 URLs, dont plusieurs pages catalogue.

Contraintes :
- Max ~100 lignes par bloc de code modifié.
- **Pas de nouvelles dépendances externes** (standard library uniquement).
- Ne pas casser les tests existants.
- On privilégie 2–3 sites **HTML simples** (tables / listes) comme POC.

---

## Étape 1 — Analyse des sites cibles

1. Ouvrir dans le navigateur au moins 3 URLs de `urls_seed_rotors.csv` :
   - Exemple candidates :
     - `https://www.autodoc.co.uk/car-parts/brake-disc-10132`
     - `https://www.mister-auto.com/brake-discs/`
     - `https://www.powerstop.com/product-category/brake-rotors/` (si HTML exploitable)
2. Pour chaque site candidat, identifier :
   - le conteneur de liste des produits (table `<table>`, `<ul>`, `<div class="product-list">`…),
   - les champs accessibles :
     - brand / manufacturer,
     - référence / part number,
     - diamètre, épaisseur, éventuellement hauteur/offset,
     - éventuellement lien vers fiche produit détaillée.
3. Choisir **2 sites** jugés :
   - HTML statique (visible dans `view-source:`),
   - structure stable,
   - informations géométriques suffisantes pour alimenter `normalize_rotor`
     ou au moins un sous-ensemble cohérent (diamètre, thickness, brand, ref).

Documenter le choix dans `documentation/M10_2_scrape_multi_list_log.md` (section "Sites cibles").

---

## Étape 2 — Nouveau module de parsing multi-items

1. Créer un nouveau fichier :
   - `data_scraper/html_rotor_list_scraper.py`
2. Y implémenter une interface générique :

   ```python
   # data_scraper/html_rotor_list_scraper.py

   from typing import Iterable, Dict, List

   def parse_rotor_list_page(html: str, source: str) -> List[Dict]:
       """
       Parse une page catalogue de rotors et retourne une liste de dicts RAW
       (avant normalize_rotor).

       - html: contenu HTML brut de la page catalogue.
       - source: identifiant du site (ex: "autodoc", "mister-auto").

       Retour:
           Liste de dicts contenant au MINIMUM:
             - "brand_raw"
             - "catalog_ref_raw"
           et idéalement:
             - "outer_diameter_mm_raw"
             - "nominal_thickness_mm_raw"
             - autres champs si disponibles.
       """
       ...
Implémenter, dans ce fichier, des parseurs spécifiques par source :

if source == "autodoc": ...

elif source == "mister-auto": ...

lever NotImplementedError pour les autres sources.

Pour chaque parseur spécifique :

localiser les lignes/blocks produits,

extraire brand, part number, dimensions si disponibles,

construire une liste de dicts RAW cohérents avec normalize_rotor.

Étape 3 — Intégration dans le pipeline d’ingestion
Ouvrir database/ingest_pipeline.py.

Ajouter un helper pour traiter une URL de liste :

python
Copy code
from data_scraper.html_rotor_list_scraper import parse_rotor_list_page
from data_scraper.html_scraper import normalize_rotor  # déjà existant

def process_rotor_list_seed(conn, source: str, url: str) -> int:
    """
    Scrape une page catalogue listant plusieurs rotors et insère chaque rotor.
    Retourne le nombre d'insertions effectives (après déduplication).
    """
    # 1. fetch_html(url)
    # 2. parse_rotor_list_page(html, source) -> list[raw_dict]
    # 3. pour chaque raw_dict:
    #       rotor = normalize_rotor(raw_dict, source=source)
    #       si non duplicat (rotor_exists):
    #           insert_rotor(conn, rotor)
    #           count += 1
    # 4. return count
Décider comment distinguer, dans urls_seed_rotors.csv, les seeds
"single product" vs "liste" :

Option simple (V1) :

ajouter une colonne kind dans urls_seed_rotors.csv (ex: product / list),

adapter iter_seed_urls('rotors') pour renvoyer aussi kind.

Option minimale (si on ne veut pas modifier le CSV pour l’instant) :

convention : source spécifique (ex: "autodoc_list") → interprété comme liste.

adapter urls_seed_rotors.csv pour utiliser source=autodoc_list pour les pages catalogue.

Dans ingest_all(group="rotors") (ou dans process_rotor_seed),
router vers process_rotor_seed ou process_rotor_list_seed selon kind / source.

Exemple (pseudo-code) :

python
Copy code
if kind == "product":
    inserted += process_rotor_seed(conn, source, url)
elif kind == "list":
    inserted += process_rotor_list_seed(conn, source, url)
else:
    # fallback / warning
Respecter strictement la limite de ~100 lignes par bloc modifié.

Étape 4 — Tests unitaires
Créer test_rotor_list_scraper.py.

Tests à couvrir :

parse_rotor_list_page pour chaque source implémentée :

cas nominal : HTML de liste (sample minimal en dur dans le test),

extraction correcte de brand, ref, dimensions,

retour d’une liste non vide,

comportement sur HTML vide / partiellement invalide.

process_rotor_list_seed :

avec un fetch_html mocké renvoyant un HTML fixe,

vérification que :

normalize_rotor est appelé pour chaque item,

insert_rotor est appelé seulement pour les non-duplicats (dédup M9).

Ne pas casser les tests existants :

pytest doit rester vert (M1–M10 + nouveaux tests).

Étape 5 — Run d’ingestion ciblé et vérification
Mettre à jour urls_seed_rotors.csv pour marquer les seeds multi-list
(par kind ou source spécifique) sur les 2 sites sélectionnés en Étape 1.

Exécuter :

bash
Copy code
python scrape_and_ingest.py --only rotors
Vérifier, via SQLite :

bash
Copy code
sqlite3 database/bbk.db "SELECT COUNT(*) FROM rotors"
Objectif : augmentation nette du nombre de rotors vs état pré-10.2.

Documenter le COUNT avant / après dans le log de mission.

Vérifier que le clustering M10 fonctionne toujours :

bash
Copy code
python -m rotor_analysis.clustering
Loaded N rotors avec N >> 47

clusters cluster_count > avant,

pas de crash.

Étape 6 — Documentation
Créer documentation/M10_2_scrape_multi_list_log.md avec :

Sites ciblés et justification.

Design de parse_rotor_list_page.

Détails d’intégration dans ingest_pipeline.

Résultats :

COUNT(rotors) avant / après 10.2,

impact sur le clustering (nombre de rotors clusterisés, nombre de clusters).

Limitations :

seulement 2–3 sites supportés V1,

pas de pagination avancée,

pas de JS / API calls.

Ajouter une section 5.3 Scraping multi-list (M10.2) dans README_data_layer_BBK.md :

description haute-niveau,

exemple de flux :

catalogue HTML → parse_rotor_list_page → normalize_rotor → insert_rotor.

Étape 7 — Git
Vérifier que tous les tests passent :

bash
Copy code
pytest
Commit :

bash
Copy code
git status
git add data_scraper/html_rotor_list_scraper.py \
        database/ingest_pipeline.py \
        test_rotor_list_scraper.py \
        documentation/M10_2_scrape_multi_list_log.md \
        documentation/README_data_layer_BBK.md
git commit -m "Mission 10.2: add multi-list rotor scraping from catalog pages"
git push
Critère de succès Mission 10.2
✅ Au moins 2 sites de type catalogue réellement supportés.

✅ Nouveau module html_rotor_list_scraper.py créé et testé.

✅ ingest_all(group="rotors") sait traiter des seeds de type "liste".

✅ COUNT(rotors) dans bbk.db augmente significativement.

✅ python -m rotor_analysis.clustering fonctionne toujours.

✅ Documentation + log de mission complétés.