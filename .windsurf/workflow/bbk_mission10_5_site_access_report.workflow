bbk_mission10_5_site_access_report.workflow
Je commence Mission 10.5 – Recensement des sites accessibles et des champs disponibles.

Objectif :
- Identifier, parmi toutes les URLs de seeds du projet, les sites réellement accessibles sans navigateur headless.
- Classer les sites selon leur niveau de protection (OK, 403/404, Cloudflare/WAF, HTML vide/JS only, etc.).
- Pour les sites accessibles, détecter automatiquement quels champs de données semblent présents dans le HTML (diamètre, épaisseur, offset, poids, bolt pattern, fitment véhicule, etc.).
- Produire un rapport JSON + Markdown pour guider les missions suivantes (scraping intensif et QA manuelle ciblée).

Contraintes générales :
- Ne pas ajouter de dépendances externes : stdlib Python uniquement.
- Ne pas modifier le schéma de la base SQLite ni casser le pipeline existant.
- Ne pas modifier les scrapers/normalizers existants (M2–M7, M10.2, M10.3). Cette mission est un audit, pas une refonte.
- Le code ajouté doit être testable, avec au moins quelques tests unitaires sur la logique de classification / détection de champs.

Plan d’action :

1. Lecture des seeds existants
   - Localiser tous les fichiers de seeds existants dans le repo, notamment :
     - data_scraper/exporters/urls_seed_rotors.csv
     - data_scraper/exporters/urls_seed_pads.csv (si existe)
     - data_scraper/exporters/urls_seed_vehicles.csv (si existe)
     - data_scraper/exporters/urls_seed_hoses.csv ou équivalent (si existe)
   - Écrire une fonction utilitaire `collect_seeds()` qui retourne une liste de dicts normalisés :
     - { "kind": "rotor"|"pad"|"vehicle"|"hose", "source": "...", "url": "...", "page_type": "product"|"list"|...? }
   - Cette fonction sera placée dans un nouveau module dédié à l’audit (cf. étape 2).

2. Nouveau module d’audit d’accessibilité
   - Créer un nouveau module, par exemple : `tools/site_access_audit.py` (ou sous un namespace similaire déjà utilisé pour les outils internes).
   - Dans ce module, implémenter au minimum :
     - `collect_seeds()` : voir étape 1.
     - `probe_url(seed) -> dict` :
       - Utiliser stdlib (urllib.request) pour effectuer un GET avec :
         - timeout raisonnable (5–10s)
         - User-Agent réaliste type navigateur.
       - Retourner un dict du type :
         - {
             "kind": ...,
             "source": ...,
             "url": ...,
             "domain": ...,
             "status_code": 200|403|404|...|None,
             "error": "...",   # si exception réseau
             "suspected_bot_protection": True|False,
             "html_sample_path": "...",  # optionnel si on sauvegarde une copie,
           }
       - Considérer comme “suspected_bot_protection” les cas suivants :
         - HTTP 403/503
         - HTML contenant des signatures typiques : "Cloudflare", "Attention Required", "enable JavaScript", "captcha"
     - `analyze_html_fields(kind: str, html: str) -> dict` :
       - Prendre en entrée le HTML (pour les URLs avec status_code 200).
       - Utiliser des regex / recherches simples pour déterminer quels types de champs semblent présents :
         - Pour rotors : diameter, thickness, overall_height, center_bore, bolt_hole_count, ventilation_type, directionality, rotor_weight_kg, etc.
         - Pour pads : pad_shape_id, pad_thickness, pad_length/width, friction_material, etc.
         - Pour vehicles : make, model, year_from, year_to, engine_size, body_type, etc.
         - Pour durites : hose_length, fitting_type, thread, etc. (si concerné)
       - Retourner un dict binaire / booléen, par exemple :
         - {
             "diameter_mm": True/False,
             "thickness_mm": True/False,
             "offset_mm": True/False,
             "fitment_vehicle": True/False,
             "weight_kg": True/False,
             ...
           }
       - Pas besoin d’être parfait : l’idée est d’identifier les sites où les champs sont clairement présents dans le HTML brut.
     - `run_audit() -> dict` :
       - Orchestrer : collecte des seeds → probe_url pour chacune → analyse HTML pour les status_code 200.
       - Construire une structure agrégée par (kind, domain, source).
       - Écrire les résultats dans :
         - `documentation/M10_5_site_access_report.json`
         - `documentation/M10_5_site_access_report.md`

3. Sauvegarde optionnelle des HTML
   - Pour les URLs avec `status_code == 200` et `suspected_bot_protection == False`, ajouter une option pour sauvegarder un échantillon du HTML :
     - Dans un répertoire dédié, par exemple : `artifacts/site_html_samples/<kind>/<domain>/...`
   - Le chemin de ce fichier pourra être stocké dans les résultats JSON pour aider à des missions ultérieures (QA manuelle ou création de nouvelles fixtures).

4. Rapport Markdown détaillé
   - Générer automatiquement un rapport Markdown : `documentation/M10_5_site_access_report.md`.
   - Pour chaque `kind` (rotor, pad, vehicle, hose) :
     - Un tableau avec colonnes :
       - source
       - domain
       - url_sample (une seule URL représentative par domaine/source)
       - status_code
       - suspected_bot_protection (Oui/Non)
       - html_saved (Oui/Non)
       - champs détectés (liste courte : ex. “diameter, thickness, bolt_pattern”)
   - Ajouter une section synthèse en haut du fichier, du type :
     - Nombre total de seeds
     - Nombre de domaines distincts
     - Nombre de domaines accessibles sans protection
     - Nombre de domaines avec protection probable (403/Cloudflare/etc.)
     - Pour les domaines accessibles : récapitulatif des champs les plus fréquents et des manques (ex: “offset_mm rarement présent”).

5. Tests unitaires
   - Créer `test_site_access_audit.py` avec au moins :
     - Tests sur `analyze_html_fields()` avec quelques HTML minimaux simulant :
       - rotor avec diamètre + épaisseur
       - rotor avec offset + bolt_hole_count
       - vehicle avec make/model/year
     - Tests sur la logique de classification bot / non-bot:
       - HTML avec “Cloudflare” → suspected_bot_protection == True
       - HTML normal → False
   - Pas besoin de tests réseau end-to-end (les vrais sites peuvent changer / être down). La logique de parsing / classification doit être testée localement sur des samples.

6. Exécution et artefacts
   - Ajouter un petit CLI dans `tools/site_access_audit.py` :
     - `if __name__ == "__main__": run_audit()`
   - Lancer l’audit une fois dans le workflow, pour produire les rapports réels.
   - Vérifier que :
     - `documentation/M10_5_site_access_report.json` est généré et bien formé.
     - `documentation/M10_5_site_access_report.md` contient au moins :
       - Une section synthèse
       - Au moins un tableau pour les rotors (et autres kinds si seeds présents).

7. Documentation et log de mission
   - Créer `documentation/M10_5_site_access_audit_log.md` qui décrit :
     - Objectif de la mission
     - Description rapide du module `tools/site_access_audit.py`
     - Format du JSON et du Markdown générés
     - Résumé quantitatif (combien de sites bloqués / accessibles, quels champs les plus fréquents, etc.).
   - Mettre à jour `documentation/README_data_layer_BBK.md` :
     - Ajouter une sous-section 5.x “Audit d’accessibilité des sites (M10.5)” avec :
       - Un lien vers le rapport
       - Un résumé de la méthode
       - Comment utiliser ce rapport pour choisir les prochaines cibles de scraping intensif ou de QA manuelle.

8. Git
   - Ajouter les nouveaux fichiers et modifications :
     - `tools/site_access_audit.py`
     - `test_site_access_audit.py`
     - `documentation/M10_5_site_access_audit_log.md`
     - `documentation/M10_5_site_access_report.json`
     - `documentation/M10_5_site_access_report.md`
   - Commit message proposé :
     - `Mission 10.5: site access audit and field availability report`
