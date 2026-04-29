# Checklist de passation (anti-perte / anti-regression)

Derniere mise a jour: 2026-04-29

## A. Debut de fil
- Lire endoff.md (entree courte).
- Lire handoff.md (contexte detaille).
- Confirmer l'etat git (fichiers modifies, conflit, propre/sale).
- Identifier les risques ouverts et hypotheses en cours.

## B. Pendant le travail
- Noter les decisions importantes dans handoff.md (pas seulement en memoire locale).
- Distinguer clairement: fait verifie / fait non verifie.
- En cas de changement sensible: ajouter une verification minimale executable.

## C. Fin de fil (obligatoire)
- Mettre a jour handoff.md:
  - changements reels
  - fichiers impactes
  - verification effectuee
  - risques restants
  - prochaine action recommandee
- Mettre a jour endoff.md en dernier:
  - statut global
  - reprise en 30 secondes
  - priorite immediate
- Verifier coherence entre les deux fichiers (pas de contradiction).

## D. Regles de qualite
- Pas de phrase floue type "normalement" sans preuve.
- Pas de suppression de contexte utile sans remplacement.
- Si une verification n'a pas pu etre executee, l'ecrire explicitement.
