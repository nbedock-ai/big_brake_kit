# bbk_mission10_1_expand_rotor_seeds.workflow

## Mission 10.1 — Expansion massive des seeds rotors

Objectif :
  Multiplier le volume de rotors disponibles avant 10.2 (scraping multi-list)
  et 10.3 (scraping systématique par véhicules), afin de construire une base
  de données suffisamment large pour alimenter M11 (sélection maîtres).

Règles :
  - Ne pas modifier la structure du data layer (M1–M9 stables).
  - Ajouter uniquement des seeds dans data_seed_url.txt et urls_seed_rotors.csv.
  - Ne jamais dépasser 100 lignes de modifs par bloc.
  - Les seeds doivent pointer des pages listant soit 1 rotor soit N rotors.
  - Les URLs peuvent contenir pagination.
  - Le code d’ingestion reste inchangé : on enrichit la matière première.

Étapes :

1. Ouvrir :
   - data_seed_url.txt
   - data_scraper/exporters/urls_seed_rotors.csv

2. Ajouter toutes les URLs suivantes (une par ligne dans urls_seed_rotors.csv) :
   - https://www.autodoc.co.uk/car-parts/brake-disc-10132
   - https://www.mister-auto.com/brake-discs/
   - https://www.carparts.com/brake-disc
   - https://www.partsgeek.com/parts/brake-rotor.html
   - https://www.summitracing.com/search/part-type/brake-rotors
   - https://www.fcpeuro.com/products/?keywords=brake+rotor
   - https://www.bremboparts.com/europe/en/catalogue/discs
   - https://www.dba.com.au/parts/search-products/?category=disc-rotors
   - https://ebcbrakes.com/products/brake-discs/
   - https://www.otto-zimmermann.de/en/products/brake-discs/
   - https://www.stoptech.com/products/brake-rotors/
   - https://www.powerstop.com/product-category/brake-rotors/
   - https://centricparts.com/catalog/brake-rotors
   - https://www.wagnerbrake.com/products/brake-rotors.html
   - https://www.raybestos.com/brake-rotors
   - https://www.trwaftermarket.com/en/catalogue/braking/disc-brakes/brake-discs/
   - https://www.boschautoparts.com/en/auto/brakes/brake-rotors
   - https://www.acdelco.com/auto-parts/brakes/brake-rotors
   - https://parts.ford.com/shop/en/us/brake-rotors
   - https://www.mopar.com/en-us/shop/parts/brakes/brake-rotors.html
   - https://www.wilwood.com/BrakeRotors/
   - https://apracing.com/products/race-car/brake-discs
   - https://www.ferodoracing.com/products/brakes/discs/
   - https://www.autozone.com/brakes-and-traction-control/brake-rotor

3. Ajouter ces nouvelles lignes dans data_seed_url.txt :
   - exporters/urls_seed_rotors.csv   # déjà présent, mais confirmer la présence
   (ne pas supprimer les anciens seeds)

4. Ne rien modifier dans ingest_pipeline.py.

5. Exécuter :
   python scrape_and_ingest.py --only rotors

6. Vérifier :
   - database/bbk.db → table rotors contient beaucoup plus que 47 modèles
   - sans doublons (dédup V1 toujours active)

7. Documenter :
   - Ajouter une section dans README_data_layer_BBK.md → "10.1 Expanded Rotor Seeds"
   - Décrire la nouvelle liste de sources et leur rôle.

8. Commit :
   git commit -am "Mission 10.1: massive expansion of rotor seed URLs"
   git push