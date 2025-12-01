# .windsurf/workflow/bbk_mission10_3_impl_multi_list_sites.workflow

You are Sonnet running inside Windsurf on the BigBrakeKit project.

Your role: implement **production-ready parsers** for rotor catalog list pages, based on the POC framework from Mission 10.2. This mission is 10.3 and must be completed BEFORE Mission 11 (master rotor selection).

Goal:
- Turn the existing templates in `data_scraper/html_rotor_list_scraper.py` into REAL parsers for multiple sources:
  - `autodoc`
  - `mister-auto`
  - `powerstop`
- Wire them into the existing ingestion pipeline and tests.
- Keep everything within existing constraints (stdlib only, max ~100 LOC per function, no DB schema change).

-------------------------------------------------------------------------------
## Étape 0 – Lecture du contexte

1. Open and read carefully:
   - `documentation/README_data_layer_BBK.md`
     - Pay special attention to sections:
       - 4.x (ingest_all pipeline, dedup M9)
       - 5.0 (rotor analysis overview)
       - 5.2 (Mission 10.1 seeds expansion)
       - 5.3 (Mission 10.2 multi-list framework)
   - `documentation/M10_2_scrape_multi_list_log.md`
   - `data_scraper/html_scraper.py`
     - Focus on `normalize_rotor()` and rotor-related helpers.
   - `data_scraper/html_rotor_list_scraper.py`
     - Focus on:
       - `parse_rotor_list_page()`
       - `parse_autodoc_list()`
       - `parse_misterauto_list()`
       - `parse_powerstop_list()`
       - `SimpleTableParser`
       - `extract_dimension()`, `clean_text()`
   - `database/ingest_pipeline.py`
     - Focus on:
       - `iter_seed_urls()`
       - `process_rotor_seed()`
       - `process_rotor_list_seed()`
       - `rotor_exists()`
       - `ingest_all()`
   - `data_scraper/exporters/urls_seed_rotors.csv`
     - Check `source` and `page_type` values for `autodoc`, `mister-auto`, `powerstop`.

2. Summarize for yourself (no need to write it out) the data flow for rotors:
   - seeds CSV → `iter_seed_urls` → router product vs list → `process_rotor_*` → `normalize_rotor` → dedup → `insert_rotor` → DB.

-------------------------------------------------------------------------------
## Étape 1 – Préparer des fixtures HTML locales pour tests

Objective: never depend on live HTTP for tests. Download one representative HTML page per site and store it as fixtures.

For each source in `["autodoc", "mister-auto", "powerstop"]`:

1. Identify the URL already present in `urls_seed_rotors.csv` with:
   - `source` = that site
   - `page_type` = `list`.

2. In a **one-off manual step** inside the project (you can use `requests` in a small helper script), download the raw HTML of the catalog page and save it as a fixture:

   - Create directory if not already present:
     - `tests/fixtures/rotor_lists/`
   - Save as:
     - `tests/fixtures/rotor_lists/autodoc_list_01.html`
     - `tests/fixtures/rotor_lists/misterauto_list_01.html`
     - `tests/fixtures/rotor_lists/powerstop_list_01.html`

   Requirements:
   - Raw HTML as returned by the site (no manual edits).
   - Single file per site is enough for this mission.

3. Make sure these fixtures are **not** committed in `.gitignore` (for the purpose of this mission we consider them versioned test assets).

-------------------------------------------------------------------------------
## Étape 2 – Implémenter parseurs site-spécifiques multilist

Goal: implement real extraction logic for each of the 3 sites, using only Python stdlib (`re`, `html.parser`, `html` etc.), and returning raw dicts compatible with `normalize_rotor()`.

General constraints:
- Max ~80–100 lines per parser function.
- Use helpers already present:
  - `clean_text(text)`
  - `extract_dimension(text, kind)`
  - `SimpleTableParser` if the HTML is table-like.
- Do NOT hit the network in the parser functions (they receive `html: str` only).

For each site:

### 2.1 AutoDoc – `parse_autodoc_list(html: str) -> List[Dict]`

1. Inspect `tests/fixtures/rotor_lists/autodoc_list_01.html`.
2. Identify product containers:
   - e.g. repeating `<div>` / `<li>` nodes containing rotor attributes.
3. For each product, extract at minimum:
   - Brand (e.g. `"BREMBO"`, `"TRW"`)
   - Catalog reference / part number (unique SKU for dedup key).
   - Outer diameter in mm (string from which `extract_dimension(..., "diameter")` can parse a float).
   - Nominal thickness in mm.
   - Optionally:
     - Overall height / hat height / offset if easily available.
4. Build raw dicts following the expectations of `normalize_rotor()`:
   - Use keys consistent with existing rotor parsing (check `html_scraper.py`):
     - Examples (adjust to actual expectations):  
       - `"brand_raw"`  
       - `"catalog_ref_raw"`  
       - `"outer_diameter_mm_raw"`  
       - `"nominal_thickness_mm_raw"`  
       - `"overall_height_mm_raw"` (optional)  
       - `"hat_height_mm_raw"` (optional)  
       - `"source"` or `"source_raw"` if expected.
5. Implement `parse_autodoc_list(html: str) -> List[Dict]` so that:
   - It returns a **non-empty list** on the fixture.
   - It is robust to minor HTML noise (extra whitespace, line breaks, etc.).
   - It never raises if one item is malformed: skip that item and continue.

### 2.2 Mister-Auto – `parse_misterauto_list(html: str) -> List[Dict]`

Same pattern as AutoDoc:

1. Inspect `tests/fixtures/rotor_lists/misterauto_list_01.html`.
2. Identify list structure (cards / rows / tables).
3. Extract same core fields (brand, catalog_ref, diameter, thickness, optional heights).
4. Build raw dicts compatible with `normalize_rotor`.
5. Implement `parse_misterauto_list` using stdlib only.

### 2.3 PowerStop – `parse_powerstop_list(html: str) -> List[Dict]`

1. Inspect `tests/fixtures/rotor_lists/powerstop_list_01.html`.
2. Identify structure, extract same core fields.
3. Implement `parse_powerstop_list` with same conventions.

### 2.4 Dispatcher – `parse_rotor_list_page(html: str, source: str)`

1. Update the dispatcher so that:
   - `source == "autodoc"` → `parse_autodoc_list`
   - `source == "mister-auto"` → `parse_misterauto_list`
   - `source == "powerstop"` → `parse_powerstop_list`
2. Keep the default behavior:
   - Unknown `source` must raise `NotImplementedError` with a clear message.
3. Make sure the function stays under ~60–80 lines if possible (factor out helpers if needed).

-------------------------------------------------------------------------------
## Étape 3 – Tests unitaires spécifiques par site

File: `test_rotor_list_scraper.py`

Objectives:
- Do NOT rely on network in tests.
- Use the fixtures created in Étape 1.
- Ensure each parser returns at least one valid raw rotor dict, compatible with `normalize_rotor()`.

Actions:

1. Add small fixture loader helper if not already present:
   - Example:
     ```python
     def load_fixture(name: str) -> str:
         base = Path(__file__).parent / "fixtures" / "rotor_lists"
         return (base / name).read_text(encoding="utf-8")
     ```

2. For each site add tests:

   - `test_autodoc_list_parser_extracts_at_least_n_rotors`:
     - Load `autodoc_list_01.html`.
     - Call `parse_autodoc_list`.
     - Assert:
       - `len(rotors) >= 5` (or another minimal number, based on fixture).
       - Each rotor has non-empty `brand_raw` and `catalog_ref_raw`.
       - At least one rotor has `outer_diameter_mm_raw` and `nominal_thickness_mm_raw` not `None`.

   - `test_misterauto_list_parser_extracts_at_least_n_rotors`:
     - Same pattern.

   - `test_powerstop_list_parser_extracts_at_least_n_rotors`:
     - Same pattern.

3. Add one integration-style test that checks compatibility with `normalize_rotor`:
   - Pick one rotor from each list.
   - Pass it through `normalize_rotor(raw, source="...")`.
   - Assert:
     - No exception is raised.
     - Required normalized fields (diameter, thickness) are not `None`.

4. Run tests:
   - Prefer `python -m pytest test_rotor_list_scraper.py` (or equivalent).
   - Fix any issue until all tests PASS.

-------------------------------------------------------------------------------
## Étape 4 – Test d’ingestion partiel (optionnel mais recommandé)

Goal: verify that the pipeline really ingests multiple rotors from at least one list site, end-to-end.

1. Ensure database schema is initialized (if not already done):
   - `python -m database.init_db` or the existing documented command.

2. Run ingestion only for rotors:
   - `python scrape_and_ingest.py --only rotors`

3. After run, check rotor count:
   - `sqlite3 database/bbk.db "SELECT COUNT(*) FROM rotors;"`

4. Optionally, run a quick sanity check:
   - `sqlite3 database/bbk.db "SELECT brand, catalog_ref, outer_diameter_mm, nominal_thickness_mm FROM rotors LIMIT 20;"`

Document in the mission log whether rotor count increased compared to pre-10.3 state, and if list-based sources contribute entries (brand/source combinations coming from autodoc/mister-auto/powerstop).

-------------------------------------------------------------------------------
## Étape 5 – Documentation & log de mission

1. Create a new mission log:
   - `documentation/M10_3_impl_multi_list_parsers_log.md`
   - Content minimum:
     - Objective of the mission (10.3).
     - List of sites implemented with short notes on HTML structure and parser strategy.
     - What fields are extracted per site.
     - Summary of tests added and results.
     - Any ingestion test you ran (counts before/after).
     - Known limitations (no pagination, fragile selectors, JS-only sections ignored, etc.).
     - Ideas for future 10.3.x improvements (more sites, pagination, retry/rate-limit).

2. Update `documentation/README_data_layer_BBK.md`:
   - In section 5.3 (multi-list scraping):
     - Mark `autodoc`, `mister-auto`, `powerstop` as **implemented** (not just templates).
     - Briefly describe that these three have production parsers backed by fixtures and tests.
     - Mention that other sites remain as future work.

3. Ensure all docs remain under repository conventions (markdown, no huge code dumps).

-------------------------------------------------------------------------------
## Étape 6 – Git

1. Stage only relevant files:
   - `data_scraper/html_rotor_list_scraper.py`
   - `test_rotor_list_scraper.py`
   - `tests/fixtures/rotor_lists/*.html` (if versioned)
   - `documentation/M10_3_impl_multi_list_parsers_log.md`
   - `documentation/README_data_layer_BBK.md`
2. Commit with message:
   - `Mission 10.3: implement multi-list rotor parsers for autodoc/misterauto/powerstop`
3. Push to the appropriate remote branch.

-------------------------------------------------------------------------------
## Règles générales

- Do NOT modify:
  - DB schema files.
  - Core ingestion semantics (`insert_rotor`, `ingest_all` signatures).
- Respect previous constraints:
  - Only Python standard library in scraping/parsing code.
  - Keep each function reasonably short (~100 lines max).
- Always keep tests green before final commit.
