# bbk_mission00_git_setup.workflow
# BigBrakeKit — Mission 0
# Git Initialization + GitHub Remote Setup
# Status: Pending
# Author: Windsurf SSR

------------------------------------------------------------
# 0. Mission Identifier
M0 — Initialisation Git + configuration remote GitHub.

------------------------------------------------------------
# 1. Scope (strict)
- Initialiser le dépôt Git dans le répertoire actuel.
- Créer un .gitignore minimal.
- Effectuer un commit initial.
- Configurer le remote GitHub (HTTPS ou SSH selon la préférence utilisateur).
- Pousser la branche main vers GitHub.

Aucune modification de code du projet.  
Aucune modification d’architecture.  
Aucun scraping, aucune logique BigBrakeKit.

------------------------------------------------------------
# 2. Inputs
- Répertoire local existant : `big_brake_kit/`
- Git installé sur la machine locale.
- L’utilisateur fournit l’URL du repo GitHub vide (remote) quand demandé.

------------------------------------------------------------
# 3. Fichiers (write)
- `.gitignore`
- Création automatique du dossier `.git/`
- Aucun autre fichier modifié.

------------------------------------------------------------
# 4. Fichiers (read-only)
- Aucun fichier du projet n'est lu ou modifié.

------------------------------------------------------------
# 5. Preconditions
- Le dossier `big_brake_kit/` existe.
- L’utilisateur confirme l’URL GitHub (SSH ou HTTPS).
- Le repo GitHub doit être vide (pas de README auto-généré).

------------------------------------------------------------
# 6. Tasks (séquentiel)
T1. Vérifier la présence de Git via `git --version`.  
T2. Initialiser un dépôt local via `git init` et `git branch -M main`.  
T3. Créer un `.gitignore` standard Python + éditeurs.  
T4. Ajouter tous les fichiers (`git add .`).  
T5. Commit initial : `"Initial BigBrakeKit repository"`.  
T6. Demander à l’utilisateur l’URL GitHub du repo vide.  
T7. Configurer le remote : `git remote add origin <URL>`.  
T8. Pousser vers GitHub : `git push -u origin main`.  
T9. Confirmer la réussite (retour Git non erroné).

------------------------------------------------------------
# 7. Commands à exécuter (générées par Windsurf)
Windsurf doit produire un bloc unique contenant exactement :

git --version
git init
git branch -M main

création .gitignore
(write minimal ignore)

git add .
git commit -m "Initial BigBrakeKit repository"

l’utilisateur fournit l’URL :
git remote add origin <URL fournie>
git push -u origin main

markdown
Copy code

Aucune autre commande.

------------------------------------------------------------
# 8. Deliverables
- `.gitignore` correctement généré.
- Dépôt Git initialisé localement.
- Remote GitHub configuré.
- Branche `main` poussée avec succès.

------------------------------------------------------------
# 9. Logs obligatoires
L’utilisateur doit fournir :
- la sortie de `git push -u origin main`
- ou toute erreur reçue.

Windsurf analyse les logs et corrige si nécessaire.

------------------------------------------------------------
# 10. Success Criteria
- `git status` ne montre aucun fichier en attente.
- `git remote -v` affiche le remote.
- GitHub contient l’arborescence complète du projet BigBrakeKit.

------------------------------------------------------------
# END OF WORKFLOW