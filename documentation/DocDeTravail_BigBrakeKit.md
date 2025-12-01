# **DocDeTravail_BigBrakeKit.md**

## **0. Vision**

Créer un **système de freins performance universel**, constitué de :

* **3 étriers standardisés** (2 pistons, 4 pistons, 6 pistons)
* **1 ou 2 plaquettes standardisées**
* **Une banque de disques maîtres** (15–25 rotors existants du marché)
* **Brackets CNC spécifiques au véhicule**

Le kit vendu au client comprend **toujours** : étriers + plaquettes + disques + bracket.
Toutes les pièces sont **produites ou commandées à la demande** — pas d’inventaire permanent.

Objectif : offrir des kits big brake adaptables à 95% des véhicules, avec un minimum de composants universels.

---

# **1. Architecture du produit**

## **1.1 Étriers universels (2P / 4P / 6P)**

Trois modèles fixes :

* **2 Pistons**

  * Marché volumique (compactes, daily).
  * Entrée de gamme performance.
  * Faible coût, forte marge.

* **4 Pistons**

  * Standard polyvalent.
  * Cœur de l’offre pour sport compact et berlines.

* **6 Pistons**

  * Segment premium (sportives, SUV, pickups).
  * Capacité thermique et esthétique.

Les 3 étriers :

* Aluminium 6061 ou 7075.
* Deux moitiés usinées CNC.
* Dimensionnés **autour d’une plaquette standard** → compatibilité totale entre familles de disques.

---

## **1.2 Plaquette standardisée**

Choisir 1–2 modèles répandus (ex. Porsche/Brembo/AMG).

Critères :

* géométrie stable,
* surface balayée élevée,
* disponibilité constante,
* compatibilité thermique élevée.

Toutes les géométries internes des étriers (ponts, dégagements, largeur gorge, placement pistons) sont dérivées de cette plaquette.

---

## **1.3 Banque de disques maîtres**

Sélection de **15–25 rotors** provenant des gammes :

* BMW / Audi / Mercedes
* Porsche / Infiniti
* Toyota / Honda
* Ford / GM
* Subaru / Range Rover

Ces disques sont choisis pour couvrir :

* diamètres 280 → 390 mm
* épaisseurs 22 → 36 mm
* hauteurs chapeau variées
* offsets multiples
* différentes exigences thermiques

Chaque véhicule client se voit attribuer le **disque optimal dans cette banque**, indépendamment du disque d’origine du véhicule.

---

## **1.4 Brackets CNC sur mesure**

Fonction :

* relier étrier universel ↔ knuckle du véhicule
* positionner la plaquette sur la zone balayée du disque maître choisi
* corriger l’offset nécessaire
* respecter les dégagements roue / barillet

Brackets générés automatiquement via modèles paramétriques.

---

## **1.5 Production à la demande (mention unique)**

Tous les éléments du kit (étriers, brackets, disques, plaquettes) sont soit :

* usinés au moment de la commande,
* ou commandés au fournisseur juste-in-time.

Pas de stockage massif.

---

## 1.x Contraintes hydrauliques

Chaque famille d’étriers (2P, 4P, 6P) existera en plusieurs variantes hydrauliques correspondant à des surfaces totales de pistons différentes. Le corps d’étrier reste identique, mais le diamètre des pistons change pour respecter le rapport hydraulique du véhicule (surface pistons / surface maître-cylindre).

Structure prévue :
- 4P-S : petite surface, pour véhicules légers ou maître-cylindre petit diamètre
- 4P-M : surface standard, cœur de marché
- 4P-L : grande surface, pour berlines lourdes / SUV

Cette notion n’est pas incluse dans la base de données V1. Un module hydraulique séparé fera le mappage véhicule → segment hydraulique (S/M/L) en V2.




---

# **2. Pipeline complet**

---

## **2.1 Étape 1 — Variables à scraper (DB de rotors)**

### **Rotors**

* outer_diameter_mm
* nominal_thickness_mm
* discard_thickness_mm
* hat_height_mm
* overall_height_mm
* center_bore_mm
* bolt_circle_mm
* bolt_hole_count
* rotor_weight_kg
* mounting_type (1-piece / 2-piece / floating / full cast)
* ventilation_type (vented/solid)
* directionality (non-directional / left/right)
* pad_swept_area_mm2 (si dispo)
* offset_mm (si dispo)

### **Plaquettes**

* shape_id (FMSI / OEM)
* length_mm
* height_mm
* thickness_mm
* backing_plate_type
* swept_area_mm2

### **Véhicule (bracket)**

* hub bolt pattern (entraxe / diamètre)
* knuckle points (entraxe, orientation)
* max rotor diameter possible
* wheel inner barrel clearance
* caliper offset target
* rotor thickness acceptable

---

## **2.2 Étape 2 — Scraping + Vision**

Pipeline :

1. Crawl catalogues fabricants (HTML quand possible).
2. Extraction via BeautifulSoup.
3. Si table non extractible → screenshot page → extraction Vision via Sonnet.
4. Normalisation → JSON schema universel.
5. Insertion DB (SQLite ou Postgres).

Outils :

* Requests / Playwright
* BeautifulSoup
* Sonnet Vision
* Windsurf workflows

---

## **2.3 Étape 3 — Analyse & Sélection des “rotors maîtres”**

Objectifs :

* Regrouper les rotors du marché par familles géométriques.
* Identifier quelles géométries couvrent le plus d’offsets et diamètres.
* Sélectionner 15–25 rotors maîtres.

Output :

* liste finale de rotors maîtres,
* tableau couvrant la gamme :

  * petits disques → compactes
  * moyens → sport/berlines
  * grands → SUV/pickups

---

## **2.4 Étape 4 — Design des étriers (2P / 4P / 6P)**

Input :

* plaquette standard
* plage géométrique compatible définie par la banque de rotors
* contraintes hydrauliques
* rigidité requise

Output :

* 3 modèles paramétriques STEP
* fichiers CNC pour l’usinage des moitiés
* notes de tolérances et gabarits

Les étriers sont fixes : aucune variation entre clients.

---

## **2.5 Étape 5 — Génération automatique des brackets**

Inputs :

* modèle du véhicule
* disque maître sélectionné
* étrier choisi (2P/4P/6P)
* offset calculé
* orientation et entraxes du knuckle

Pipeline :

1. Calcul position géométrique étrier ↔ disque.
2. Génération sketch paramétrique.
3. Export STEP.
4. Optionnel : export G-code (mais STEP suffit).

---

## **2.6 Étape 6 — Production / assemblage**

Exécution :

* Usinage étrier (2P/4P/6P)
* Usinage bracket
* Commande disque et plaquettes
* Assemblage final + peinture four/anodisation
* Test montage rapide
* Expédition du kit

Tout est déclenché **uniquement après commande client**.

---

## **2.7 Étape 7 — Produit final livré**

Contient systématiquement :

* 1 paire d’étriers (2P / 4P / 6P)
* 1 set de plaquettes standardisées
* 1 set de disques sélectionnés dans la banque maîtresse
* 1 bracket CNC sur mesure pour le véhicule
* visserie + instructions
* options : durites tressées, liquide haute température

---

# **3. Structure de projet recommandée**

```
big_brake_kit/
│
├── data_scraper/
│   ├── html_scraper.py
│   ├── vision_scraper.py
│   ├── schema_rotor.json
│   ├── schema_pad.json
│   └── exporters/
│
├── database/
│   ├── init.sql
│   ├── models/
│   └── ingest_pipeline.py
│
├── rotor_analysis/
│   ├── clustering.py
│   ├── select_master_rotors.py
│   └── rotor_families.json
│
├── caliper_design/
│   ├── caliper_2p.step
│   ├── caliper_4p.step
│   ├── caliper_6p.step
│   └── notes/
│
├── bracket_generator/
│   ├── compute_offsets.py
│   ├── generate_bracket_parametric.py
│   └── outputs/
│
└── documentation/
    └── DocDeTravail_BigBrakeKit.md
```

---

# **4. Prochaines étapes immédiates**

1. Définir la liste définitive de rotors maîtres (15–25).
2. Construire le scraper HTML V1.
3. Ajouter pipeline Vision.
4. Normaliser DB.
5. Sélectionner la plaquette maître.
6. Lancer le design paramétrique 2P / 4P / 6P.
7. Développer le générateur automatique de brackets.





### Extension hydraulique prévue (V2)

Le schéma `VehicleBrakeFitment` ne contient volontairement aucune donnée hydraulique (pression, diamètre de ligne, surface OEM). Ces valeurs ne sont ni standardisées ni exploitables pour le design du kit.

V2 ajoutera une couche distincte `vehicle_segment_map.json` qui regroupera les véhicules en trois segments hydrauliques. Aucun champ supplémentaire n'est ajouté au schéma JSON du véhicule.



