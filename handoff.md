# Handoff - Contexte complet de passation

Derniere mise a jour: 2026-04-29
Projet: DiagPcNet

## 1) Objectif produit
DiagPcNet est une application Windows (Python) de diagnostic/reparation orientee postes clients, avec interface multi-onglets (reseau, maintenance, stockage, scripts, etc.).

## 2) Etat courant verifie
- Lancement local confirme via `python main.py`.
- Dernier code de sortie observe: 0.
- Depot sans modifications locales au moment de creation de ce fichier.

## 3) Structure fonctionnelle (haut niveau)
- Entree app: main.py
- UI: ui.py
- Fonctions reseau/diag/reparation: diagnostic.py, repair.py, repair_tools.py
- Materiel/peripheriques: hardware.py
- Utilitaires: utils.py
- Modules annexes: benchmark.py, cleaner.py, scripts_manager.py, vault.py, games.py, git_monitor.py

## 4) Regles de passation inter-fils
- Toujours mettre a jour endoff.md en dernier (etat ultra court).
- Maintenir handoff.md comme source detaillee (etat, decisions, risques, prochaines actions).
- Ne jamais supprimer une information utile sans la remplacer par une version plus precise.
- Indiquer explicitement ce qui est verifie vs ce qui est suppose.
- En cas de doute sur une regression, ajouter un test/controle de reproduction dans ce fichier.

## 5) Journal de passation
### 2026-04-29 - Onglet Projets Git (tri, logs, signatures, admin)
- Ajout du tri par clic sur les entetes de colonnes du tableau Git.
- Ajout d'une console de logs Git sous le tableau, limitee a 200 lignes.
- Hauteur de la console Git augmentee (x2) pour une meilleure lisibilite.
- Double-clic dans la console Git pour effacer les logs.
- Ajout de logs applicatifs cibles pour la gestion commit/push (etapes, succes, erreurs exploitables).
- Commit passe en signature cryptographique (`git commit -S`) au lieu du simple signoff (`-s`).
- Push tente en mode signe (`git push --signed`), puis fallback non signe documente si non supporte cote serveur.
- Cas "serveur ne supporte pas --signed push" reclasse en information non critique (plus un faux bruit d'erreur).
- Verification admin renforcee avant action commit/push dans l'UI, avec tentative de relance admin.
- Verification admin stricte au demarrage dans `main.py`: fermeture si elevation impossible/refusee.

### 2026-04-29 - Initialisation
- Mise en place des fichiers de passation: endoff.md, handoff.md, passation_checklist.md.
- Objectif: reprise fiable d'un fil a l'autre sans perte de contexte ni regression silencieuse.

## 6) Risques et points de vigilance
- Les actions systeme peuvent necessiter droits admin selon la fonctionnalite.
- Les regressions UI peuvent passer inapercues sans scenario de verification minimale.

## 7) Verification minimale anti-regression
- Lancer application: `python main.py`
- Ouvrir les onglets critiques et verifier absence d'erreur bloquante.
- Si changement fonctionnel: documenter resultat attendu + resultat observe.

## 9) Tests executes sur ce lot
- Verification statique: aucune erreur detectee sur `ui.py`, `git_monitor.py`, `main.py`.
- Verification runtime non effectuee ici (GUI non jouee pas a pas dans ce lot).

## 8) Prochaines actions candidates
- Maintenir ce journal a chaque lot de modifications.
- Ajouter, si necessaire, une section "tests executes" plus detaillee pour les futurs chantiers.
