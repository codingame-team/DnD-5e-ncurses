CONTRIBUTING.md

Merci de votre intérêt pour contribuer à DnD-5e-ncurses ! Ce document explique comment proposer des corrections, des fonctionnalités et des améliorations.

1. Avant de commencer
---------------------
- Lisez le fichier `README.md` pour comprendre le projet, son architecture et comment lancer le jeu.
- Recherchez les issues ouvertes pour voir si quelqu’un a déjà signalé le même problème ou proposé la même idée.
- Ouvrez une issue pour discuter d'une grosse fonctionnalité avant d'implémenter.

2. Signaler un bug (Issue)
--------------------------
Lorsque vous ouvrez une issue, merci d’inclure :
- Un titre clair et concis.
- Une description du comportement attendu et du comportement observé.
- Étapes pour reproduire le bug (commandes, environnement, version de Python).
- Extraits de logs ou captures d’écran si pertinent.

3. Proposer un changement (Pull Request)
---------------------------------------
- Forkez le dépôt et créez une branche dédiée : `fix/description-courte` ou `feat/description-courte`.
- Écrivez des commits clairs et atomiques. Préférez des messages de commit du type : `feat: ajouter gestion des potions` ou `fix: corriger sauvegarde après achat`.
- Ajoutez des tests si possible (logique de jeu, sauvegarde, shop).
- Mettez à jour le `README.md` si vous modifiez le comportement utilisateur ou ajoutez une nouvelle dépendance.
- Dans votre PR, décrivez brièvement : but du changement, comportement avant/après, instructions pour tester.

4. Style et qualité du code
--------------------------
- Langage : Python 3.8+.
- Respectez le style PEP8 autant que possible.
- Utilisez des noms explicites pour les fonctions et variables.
- Ajoutez des docstrings (format simple) pour les fonctions publiques.
- Ne changez pas la mise en page générale du projet sans en discuter (indentation, nommage global).

5. Tests
--------
- Si vous ajoutez de la logique critique (sauvegarde, achat/vente, équipement), ajoutez des tests unitaires. Le dépôt n’inclut pas forcément un framework de test aujourd’hui ; pytest est recommandé.
- Exemple d’exécution des tests (si vous ajoutez pytest) :

  python -m pytest

6. Exécution locale
-------------------
- Créez un environnement virtuel : `python3 -m venv .venv` puis `source .venv/bin/activate` (macOS/Linux).
- Installez les dépendances si un `requirements.txt` existe : `pip install -r requirements.txt`.
- Lancez le jeu avec : `python main.py`.

7. Communication
----------------
- Pour les grosses modifications, ouvrez d’abord une issue pour discussion.
- Soyez poli et constructif dans les discussions. Respectez les autres contributeurs.

8. Licence
---------
- Par défaut le dépôt n’inclut pas de licence. En soumettant une PR, assumez que l’auteur principal acceptera la licence choisie (idéalement MIT) — contactez le mainteneur si vous avez des doutes.

9. Remarques finales
-------------------
Merci pour votre aide ! Les petites contributions (corrections typographiques, clarification du README, tests) sont très appréciées et facilitent l’évolution du projet.

