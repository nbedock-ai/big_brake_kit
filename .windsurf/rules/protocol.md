---
trigger: manual
---

# BigBrakeKit — Local Protocol (Minimal)

## 0. Objet
Règles minimales applicables à toutes les missions de ce repo.
Les détails, contraintes et étapes se trouvent dans les fichiers `.workflow` de `.windsurf/workflow/`.

---

## 1. Règle principale
Tu suis toujours le workflow explicitement demandé (ex: `bbk_mission01_bootstrap_and_repository_initialization.workflow`).
S’il y a conflit entre ce fichier et un workflow, le workflow prévaut.

---

## 2. Périmètre fichiers
Avant d’écrire du code, tu indiques dans le chat :
- la liste des fichiers que tu comptes modifier.

Tu ne touches pas à d’autres fichiers **sauf** si le workflow l’exige ou si l’utilisateur te le demande explicitement.

---

## 3. Taille des modifications
Pour chaque réponse où tu génères du code :
- limite-toi à **≤ 100 lignes de code effectif** (hors commentaires et blancs) par fichier.

Si tu as besoin de plus, tu le dis et tu découpes en plusieurs étapes.

---

## 4. Journal des modifications
En fin de mission (ou de gros bloc de travail), tu produis un court récapitulatif dans le chat :

- fichiers modifiés,
- fonctions ou sections touchées,
- but des changements.

Aucun format particulier imposé, 5–10 lignes suffisent.

---

## 5. Tests (souples)
Quand c’est pertinent, tu proposes **au moins un** test simple (commande Python, script, etc.) pour vérifier que ton code s’exécute sans erreur.
Tu ne bloques pas si le test n’est pas encore exécuté : tu continues une fois que l’utilisateur a donné le retour.

---

## 6. Style et limites
- Pas de refactor massif non demandé.
- Pas d’introduction de nouvelles dépendances sans le dire clairement.
- Pas de suppression de fichiers sans demande explicite.

Le reste est géré par les workflows spécifiques (bbk_missionXX).

---

## END
