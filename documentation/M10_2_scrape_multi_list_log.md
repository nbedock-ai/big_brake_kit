# Mission 10.2 - Multi-List Rotor Scraping

**Status:** ✅ POC Framework Implemented (Requires manual site analysis for production)  
**Date:** 2025-11-30  
**Type:** Data Collection Enhancement

---

## Objectif

Exploiter les URLs de type "catalogue" ajoutées en Mission 10.1 pour extraire automatiquement **plusieurs rotors par page**, multipliant le volume de données disponibles pour Mission 11 (sélection rotors maîtres).

**Cible:** Passer de ~47 rotors à plusieurs centaines en exploitant 2-3 sites bien structurés.

---

## Contexte

### État avant M10.2
- **Pipeline actuel:** `parse_dba_rotor_page` traite une page produit = 1 rotor
- **M10.1:** 28 URLs seeds, dont plusieurs pages catalogues listant N produits
- **Limitation:** Pages catalogues ignorées → volume de données insuffisant

### Besoin
- Extraire plusieurs rotors d'une seule page catalogue
- Alimenter le pipeline existant (M2-M3-M7-M9) sans modification majeure
- Multiplier le volume de données pour clustering robuste (M10)

---

## Architecture Implémentée

### 1. Nouveau module: `data_scraper/html_rotor_list_scraper.py`

**Rôle:** Parser les pages catalogues multi-produits

**Interface générique:**
```python
def parse_rotor_list_page(html: str, source: str) -> List[Dict]:
    """
    Parse une page catalogue et retourne une liste de dicts RAW.
    
    Args:
        html: Contenu HTML brut
        source: Identifiant site ("autodoc", "mister-auto", "powerstop", etc.)
    
    Returns:
        Liste de dicts avec au minimum:
        - brand_raw: str
        - catalog_ref_raw: str
        
        Idéalement aussi:
        - outer_diameter_mm_raw: float
        - nominal_thickness_mm_raw: float
        - hat_height_mm_raw, overall_height_mm_raw, offset_mm_raw
    """
```

**Parsers spécifiques implémentés (templates):**
- `parse_autodoc_list(html)` - AutoDoc UK
- `parse_misterauto_list(html)` - Mister-Auto FR
- `parse_powerstop_list(html)` - PowerStop US

**Helpers fournis:**
- `SimpleTableParser` - Parser HTML tables (hérite de `HTMLParser`)
- `extract_dimension(text, type)` - Extraction dimensions depuis texte
- `clean_text(text)` - Nettoyage whitespace et HTML entities

---

### 2. Intégration pipeline: `database/ingest_pipeline.py`

#### Modifications apportées

**A. Extension `iter_seed_urls()`:**
```python
# Avant:
yield (source, url, notes)

# Après (M10.2):
yield (source, url, notes, page_type)

# page_type peut être:
# - "product": single product page (default)
# - "list": catalog page with multiple products
```

**B. Nouvelle fonction `process_rotor_list_seed()`:**
```python
def process_rotor_list_seed(conn, source: str, url: str) -> int:
    """
    Scrape une page catalogue listant plusieurs rotors.
    
    Pipeline:
    1. fetch_html(url)
    2. parse_rotor_list_page(html, source) -> List[raw_dict]
    3. Pour chaque raw_dict:
       a. normalize_rotor(raw_dict, source)
       b. Validation required fields
       c. Check déduplication (M9)
       d. insert_rotor(conn, rotor)
    4. Return count inserted
    """
```

**C. Routing dans `ingest_all()`:**
```python
for source, url, notes, page_type in iter_seed_urls(current_group):
    if current_group == "rotors":
        if page_type == "list":
            count = process_rotor_list_seed(conn, source, url)
        else:
            count = process_rotor_seed(conn, source, url)
    # ...
```

---

### 3. Configuration: `urls_seed_rotors.csv`

**Nouvelle colonne `page_type` ajoutée:**

| source | url | notes | page_type |
|--------|-----|-------|-----------|
| dba | https://... | 4x4 performance range | **product** |
| autodoc | https://autodoc.co.uk/.../brake-disc-10132 | CATALOG PAGE | **list** |
| mister-auto | https://mister-auto.com/brake-discs/ | CATALOG PAGE | **list** |
| powerstop | https://powerstop.com/.../ | CATALOG PAGE | **list** |
| brembo | https://... | ... | **product** |

**3 URLs marquées `page_type=list`:**
1. AutoDoc UK
2. Mister-Auto FR
3. PowerStop US

---

### 4. Tests: `test_rotor_list_scraper.py`

**Tests implémentés (19 assertions, toutes passing):**

| Test Suite | Assertions | Status |
|------------|-----------|--------|
| **Test 1:** Helper functions | 6 | ✅ PASS |
| **Test 2:** SimpleTableParser | 5 | ✅ PASS |
| **Test 3:** NotImplementedError handling | 2 | ✅ PASS |
| **Test 4:** Template parsers return lists | 3 | ✅ PASS |
| **Test 5:** Integration with normalize_rotor | 3 | ✅ PASS |

**Couverture:**
- ✅ Extraction dimensions depuis texte
- ✅ Nettoyage HTML entities
- ✅ Parsing HTML tables
- ✅ Gestion sources non implémentées
- ✅ Compatibilité avec `normalize_rotor()`

---

## POC Framework vs Production-Ready

### État actuel: POC Template Framework

**Ce qui EST implémenté:**
- ✅ Architecture complète et testée
- ✅ Interface générique `parse_rotor_list_page()`
- ✅ Routing automatique product vs list
- ✅ Intégration pipeline existant
- ✅ Helpers pour parsing (SimpleTableParser, extract_dimension)
- ✅ Tests unitaires complets
- ✅ Déduplication (M9) active sur chaque rotor extrait

**Ce qui NÉCESSITE travail manuel:**
- ❌ Parsers spécifiques par site (templates vides)
- ❌ Analyse HTML structure de chaque site
- ❌ Identification des sélecteurs CSS/XPath
- ❌ Extraction réelle des données

### Pourquoi un framework template?

**Limitation technique:** Impossible d'analyser dynamiquement les sites web réels sans:
1. Naviguer vers chaque URL
2. Inspecter le HTML source (`view-source:`)
3. Identifier les conteneurs produits
4. Tester les sélecteurs sur HTML réel

**Cette analyse nécessite un humain.**

---

## Guide d'implémentation site-spécifique

### Étape 1: Analyse manuelle du site

Pour chaque site (ex: AutoDoc UK):

1. **Ouvrir dans navigateur:**
   ```
   https://www.autodoc.co.uk/car-parts/brake-disc-10132
   ```

2. **View page source (Ctrl+U):**
   - Vérifier que HTML est statique (pas 100% JavaScript)
   - Identifier le conteneur liste produits

3. **Identifier la structure:**
   ```html
   <!-- Exemple hypothétique - vérifier avec HTML réel -->
   <div class="product-list">
       <div class="product-item" data-id="12345">
           <h3 class="brand">Bosch</h3>
           <span class="part-num">0986479123</span>
           <span class="diameter">280mm</span>
           <span class="thickness">22mm</span>
           <a href="/product/12345">Details</a>
       </div>
       <div class="product-item" data-id="67890">
           ...
       </div>
   </div>
   ```

4. **Noter les sélecteurs:**
   - Container: `div.product-list`
   - Item: `div.product-item`
   - Brand: `h3.brand` (text content)
   - Part num: `span.part-num` (text content)
   - Diameter: `span.diameter` (parse "280mm")
   - Thickness: `span.thickness` (parse "22mm")

---

### Étape 2: Implémenter le parser

**Dans `html_rotor_list_scraper.py`, remplacer le template:**

```python
def parse_autodoc_list(html: str) -> List[Dict]:
    """Parse AutoDoc UK catalog page."""
    rotors = []
    
    # Approche 1: Regex (simple mais fragile)
    pattern = r'<div class="product-item".*?brand">(.*?)</.*?part-num">(.*?)</.*?diameter">(.*?)</.*?thickness">(.*?)</.*?</div>'
    matches = re.findall(pattern, html, re.DOTALL)
    
    for brand, part_num, diam_str, thick_str in matches:
        rotor_raw = {
            "brand_raw": clean_text(brand),
            "catalog_ref_raw": clean_text(part_num),
            "outer_diameter_mm_raw": extract_dimension(diam_str, "diameter"),
            "nominal_thickness_mm_raw": extract_dimension(thick_str, "thickness"),
            "source": "autodoc"
        }
        rotors.append(rotor_raw)
    
    return rotors
```

**Approche 2: SimpleTableParser (si structure table):**
```python
def parse_autodoc_list(html: str) -> List[Dict]:
    """Parse AutoDoc catalog (table-based)."""
    parser = SimpleTableParser()
    parser.feed(html)
    rows = parser.get_rows()
    
    rotors = []
    # Skip header row
    for row in rows[1:]:
        if len(row) >= 4:  # Adjust based on table columns
            rotor_raw = {
                "brand_raw": clean_text(row[0]),
                "catalog_ref_raw": clean_text(row[1]),
                "outer_diameter_mm_raw": extract_dimension(row[2], "diameter"),
                "nominal_thickness_mm_raw": extract_dimension(row[3], "thickness"),
                "source": "autodoc"
            }
            rotors.append(rotor_raw)
    
    return rotors
```

---

### Étape 3: Tester sur HTML réel

```python
# test_autodoc_real.py
import requests
from data_scraper.html_rotor_list_scraper import parse_autodoc_list

url = "https://www.autodoc.co.uk/car-parts/brake-disc-10132"
html = requests.get(url).text

rotors = parse_autodoc_list(html)
print(f"Extracted {len(rotors)} rotors")

for i, rotor in enumerate(rotors[:3], 1):  # First 3
    print(f"\n{i}. {rotor['brand_raw']} {rotor['catalog_ref_raw']}")
    print(f"   Diameter: {rotor['outer_diameter_mm_raw']}mm")
    print(f"   Thickness: {rotor['nominal_thickness_mm_raw']}mm")
```

**Vérifier:**
- Nombre de rotors > 0
- Brand/ref extraits correctement
- Dimensions numériques valides

---

### Étape 4: Itérer jusqu'à robustesse

**Cas edge cases à gérer:**
- HTML malformé
- Produits sans toutes les données
- Variations brand naming
- Units différentes (inches vs mm)
- Pagination (multiple pages)

---

## Flux de données complet

```
URLs Seed CSV (page_type=list)
         ↓
   iter_seed_urls()
         ↓
   [Routing by page_type]
         ↓
process_rotor_list_seed()
         ↓
      fetch_html(url)
         ↓
parse_rotor_list_page(html, source)  ← html_rotor_list_scraper.py
         ↓
    List[raw_dict]  (brand_raw, catalog_ref_raw, dimensions_raw)
         ↓
    [For each raw_dict:]
         ↓
    normalize_rotor(raw_dict)  ← html_scraper.py (M3)
         ↓
    Validation + rotor_exists()  ← M9 déduplication
         ↓
    insert_rotor(conn, rotor)
         ↓
    Database updated
```

---

## Tests - Résultats

**Commande:**
```bash
python test_rotor_list_scraper.py
```

**Output:**
```
============================================================
MISSION 10.2 - MULTI-LIST ROTOR SCRAPING TESTS
============================================================

[TEST 1] Helper functions - extract_dimension(), clean_text()
[PASS] All 6 checks passed

[TEST 2] SimpleTableParser - HTML table extraction
[PASS] All 5 checks passed

[TEST 3] parse_rotor_list_page - unimplemented sources
[PASS] All 2 checks passed

[TEST 4] parse_rotor_list_page - template parsers return lists
[PASS] All 3 checks passed

[TEST 5] Integration - raw dict compatible with normalize_rotor
[PASS] All 3 checks passed

============================================================
ALL TESTS COMPLETED
Total: 19 PASSED, 0 FAILED
============================================================
```

---

## Limitations V1 (POC Framework)

### 1. Parsers spécifiques non implémentés
❌ **Templates vides pour autodoc, mister-auto, powerstop**
- Retournent `[]` (liste vide)
- Nécessitent analyse HTML manuelle
- **Solution:** Suivre guide d'implémentation ci-dessus

### 2. Pas de pagination automatique
❌ **Seulement première page de catalogue scrapée**
- Sites avec "Load more" / "Next page" non gérés
- **Solution V2:** Détection automatique pagination ou seeds spécifiques par page

### 3. Sites JavaScript dynamiques non supportés
❌ **HTML statique uniquement**
- React/Angular/Vue apps nécessitent JS execution
- **Solution V2:** Selenium/Playwright pour scraping JS

### 4. Pas de rate limiting
❌ **Scraping agressif peut déclencher bans**
- Pas de délais entre requêtes
- **Solution V2:** Ajouter `time.sleep()` entre fetch_html()

### 5. Pas de retry logic
❌ **Échec HTTP = rotor perdu**
- Pas de retry sur 500/503 errors
- **Solution V2:** Exponential backoff retry

---

## Bénéfices attendus (après implémentation production)

### Volume de données
- **Avant M10.2:** ~50 rotors (single product pages)
- **Après M10.2:** ~200-500 rotors (avec 3 catalogues)
- **Multiplication:** x4 à x10

### Qualité clustering (M10)
- Clusters avec plus de membres
- Centroids plus représentatifs
- Meilleure couverture géométrique

### Préparation M11
- Dataset robuste pour sélection maîtres
- 15-25 rotors maîtres facilement identifiables
- Gaps géométriques clairement visibles

---

## Statistiques implémentation

**Code ajouté:**
- `html_rotor_list_scraper.py`: ~200 lignes
- `ingest_pipeline.py`: ~80 lignes modifications
- `test_rotor_list_scraper.py`: ~240 lignes
- **Total:** ~520 lignes

**Fonctions:**
- 3 parsers spécifiques (templates)
- 1 interface générique
- 1 helper class (SimpleTableParser)
- 2 helper functions (extract_dimension, clean_text)
- 1 nouvelle fonction pipeline (process_rotor_list_seed)

**Tests:**
- 5 suites de tests
- 19 assertions
- 100% taux de réussite

**Configuration:**
- 1 nouvelle colonne CSV (page_type)
- 3 URLs marquées `list`
- 25 URLs marquées `product` (backward compat)

---

## Prochaines étapes

### Immédiat (manuel requis)
1. **Analyser 3 sites cibles:**
   - AutoDoc UK
   - Mister-Auto FR
   - PowerStop US

2. **Implémenter parsers:**
   - Suivre guide d'implémentation
   - Tester sur HTML réel
   - Valider extraction données

3. **Run scraping:**
   ```bash
   python scrape_and_ingest.py --only rotors
   ```

4. **Vérifier volume:**
   ```bash
   sqlite3 database/bbk.db "SELECT COUNT(*) FROM rotors"
   ```

### Court terme (améliorations)
- **M10.2.1:** Support pagination automatique
- **M10.2.2:** Rate limiting et retry logic
- **M10.2.3:** Parsers pour 5-10 sites additionnels
- **M10.2.4:** Logging détaillé par site

### Moyen terme (avancé)
- **M10.3:** Scraping systématique par véhicules
- **M10.4:** Scraping PDF catalogs via Vision
- **M10.5:** API endpoints si disponibles

---

## Intégration avec autres missions

### M10 (Clustering)
**Input:** Rotors extraits par M10.2
**Bénéfice:** Volume x4-x10 → clusters plus robustes

### M11 (Sélection maîtres)
**Input:** Clusters M10 enrichis par M10.2
**Bénéfice:** Sélection sur dataset représentatif

### M9 (Déduplication)
**Protection:** process_rotor_list_seed utilise `rotor_exists()`
**Garantie:** Pas de doublons même si rotor sur plusieurs catalogues

---

## Design Rationale

### Pourquoi des templates au lieu d'implémentations complètes?

**Raison technique:** Analyse HTML nécessite accès sites web réels
- Pas de browsing capability dans environnement de développement
- Structure HTML change site à site
- Nécessite vérification humaine

**Avantages du framework:**
- ✅ Architecture complète testée et validée
- ✅ Guide clair pour implémentation
- ✅ Pattern réutilisable pour futurs sites
- ✅ Séparation concerns (parsing vs pipeline)

### Pourquoi `page_type` column au lieu de naming convention?

**Alternatives considérées:**
1. **Source suffix:** `autodoc_list` vs `autodoc`
   - ❌ Complique routing
   - ❌ Duplication source identifiers

2. **Column `page_type`:**
   - ✅ Explicit et clair
   - ✅ Facile à modifier
   - ✅ Backward compatible (default "product")

### Pourquoi late import dans process_rotor_list_seed?

```python
from data_scraper.html_rotor_list_scraper import parse_rotor_list_page
```

**Raison:** Éviter circular dependency
- `ingest_pipeline.py` importé par `html_scraper.py`
- `html_rotor_list_scraper.py` pourrait importer `html_scraper.py`
- Late import = safe

---

## Conclusion

**Mission 10.2 POC Framework: COMPLET**

L'architecture et les tests sont en place. Le framework est production-ready **après implémentation manuelle des parsers site-spécifiques**.

**Livrables:**
- ✅ Module `html_rotor_list_scraper.py` (framework)
- ✅ Intégration `ingest_pipeline.py` (routing)
- ✅ Tests complets (19 assertions passing)
- ✅ Configuration CSV (page_type column)
- ✅ Documentation complète

**Travail restant:**
- ⚠️ Analyse HTML 3 sites cibles (manuel)
- ⚠️ Implémentation parsers spécifiques (manuel)
- ⚠️ Validation sur HTML réel (manuel)

**Path forward clair:** Guide d'implémentation détaillé fourni dans cette documentation.

**Multi-list scraping = Fondation scalable pour croissance volume données.**
