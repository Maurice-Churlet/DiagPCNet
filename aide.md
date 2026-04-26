# Aide DiagPcNet

## Onglet: Réseau
**DIAGNOSTIC & RÉPARATION RÉSEAU**
Cet onglet permet de résoudre les problèmes de visibilité d'un PC sur le réseau local ou l'impossibilité d'accéder à des dossiers partagés.
- **Bouton Analyser** : Vérifie l'état des services Windows (SMB, Découverte), le type de profil réseau (doit être Privé) et les règles du Pare-feu.
- **Bouton Réparer** : Applique les correctifs automatiques (réinitialisation du réseau, activation des services, correction du registre).

## Onglet: Stockage
**BENCHMARK & PERFORMANCE**
Mesurez la vitesse réelle de vos disques durs, SSD et clés USB.
- **Sélection** : Choisissez la lettre du lecteur à tester.
- **Vitesse d'écriture** : Le programme écrit un fichier temporaire de 100 Mo pour mesurer le débit.
- **Vitesse de lecture** : Le programme relit ce fichier pour mesurer la performance de lecture.
- **Interprétation** : L'outil compare vos résultats aux standards (NVMe Gen4, SSD SATA, USB 3.0) pour vous dire si votre matériel fonctionne normalement.

## Onglet: Périphériques
**AUDIT MATÉRIEL & PILOTES**
Obtenez un état de santé complet de votre machine.
- **Audit Matériel** : Affiche les infos sur le processeur, la RAM et la version exacte de Windows.
- **Périphériques USB** : Liste tous les appareils branchés (Prises USB, disques externes).
- **Pilotes** : Scanne le Gestionnaire de Périphériques à la recherche d'erreurs (point d'exclamation jaune).
- **Batterie** : (Sur PC portables) Indique le niveau d'usure et la capacité restante.

## Onglet: Projets Git
**SURVEILLANCE DES DÉPÔTS GIT**
Suivez l'état de vos projets de développement dans un dossier spécifique (ex: C:\Dev).
- **Scan Récursif** : Trouve tous les dépôts Git ayant un serveur distant (Remote).
- **Statut Local** : Indique si vous avez des modifications non commitées (Dirty).
- **Synchronisation** : Vous informe si vous êtes en avance (Ahead) ou en retard (Behind) par rapport à GitHub/GitLab.

## Onglet: Maintenance
**NETTOYAGE & RÉPARATION SYSTÈME**
Maintenez votre Windows propre et stable.
- **Nettoyage Disque** : Supprime les fichiers temporaires encombrants, le cache système et vide la corbeille.
- **Réparations (SFC/DISM)** : Lance les commandes officielles de Microsoft pour réparer les fichiers système corrompus ou l'image Windows endommagée.

## Onglet: Gestion
**PROGRAMMES & DÉMARRAGE**
Gérez ce qui tourne sur votre PC.
- **Démarrage** : Liste les logiciels qui se lancent automatiquement au démarrage de Windows. Désactivez ceux qui ralentissent votre PC.
- **Logiciels Installés** : Un inventaire complet de toutes vos applications avec leurs numéros de version.

## Onglet: Coffre
**COFFRE-FORT SÉCURISÉ (ANTI-CONTRAINTE)**
Stockez vos clés API et secrets avec une protection supplémentaire.


## Onglet: Scripts
**SCRIPTS & PRESSE-PAPIERS**
Automatisez vos tâches répétitives.
- **Mode PowerShell** : Lance un script dans une fenêtre PowerShell visible.
- **Mode Caché** : Exécute une commande sans fenêtre.
- **Mode Copie** : Met instantanément le texte choisi dans votre presse-papiers (utile pour les emails types ou les codes complexes).

## Onglet: Jeux
**ESPACE DÉTENTE & JEUX RÉTRO**
Faites une pause pendant que vos diagnostics réseau ou réparations Windows tournent.
- **Pong** : Jouez à l'un des plus anciens jeux d'arcade ! Déplacez votre raquette (à gauche) avec la molette de la souris ou les flèches haut/bas. Renvoyez la balle pour marquer contre l'ordinateur.
- **Snake** : Prenez le contrôle d'un serpent. Mangez la cible rouge pour grandir et marquer des points. Utilisez les flèches directionnelles et évitez les murs et votre propre queue.

## Onglet: Paramètres
**CONFIGURATION DE L'INTERFACE**
Personnalisez votre expérience avec DiagPcNet.
- **Visibilité des onglets** : Cochez/décochez les onglets selon vos besoins, les modifications sont appliquées automatiquement.
- **Sauvegarde** : Les préférences sont conservées pour votre prochaine utilisation.
