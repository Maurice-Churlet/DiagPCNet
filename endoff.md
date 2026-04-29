# Endoff - Point d'entree rapide

Derniere mise a jour: 2026-04-29
Projet: DiagPcNet
Statut global: EN EVOLUTION (lot Git/UI integre, verification statique OK)

## Reprise en 30 secondes
- Lire d'abord: handoff.md
- Verifier ensuite: passation_checklist.md
- Etat runtime connu: commande `python main.py` executee avec code 0.
- Etat git connu: working tree propre au moment de cette passation.

## Priorite immediate
- Valider en execution reelle les actions commit/push sur un depot de test.
- A chaque changement code: mettre a jour ce fichier (resume) + handoff.md (detail).

## Dernier lot valide
- Date: 2026-04-29
- Action: evolution onglet Projets Git (tri entetes, console logs 200 lignes, commit/push signes, verification admin)
- Impact: meilleure auditabilite des erreurs commit/push + comportement admin strict + console logs Git plus lisible
- Risque ouvert: compatibilite du push signe dependante du serveur distant (fallback non signe journalise)
