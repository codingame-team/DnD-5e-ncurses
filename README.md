# DnD-5e-ncurses

Description
-----------
DnD-5e-ncurses est un petit jeu en console utilisant ncurses (interface textuelle) où le joueur dirige un héros dans des donjons avec des rencontres aléatoires. Le jeu propose un menu principal, un château (shop) pour acheter/vendre équipements, un inventaire avec gestion d'armes/armures/potions et un système de sauvegarde automatique en JSON.

Architecture (fichiers principaux)
----------------------------------
- `entities.py`  : Définitions des classes Entity, Player, Monster et objets liés (armes, armures, potions).
- `game.py`      : Logique du jeu (boucle principale, combats, rencontres aléatoires, gains de trésor).
- `ui_curses.py` : Interface utilisateur basée sur curses ; menus, affichage du donjon, inventaire, château et shop.
- `main.py`      : Point d'entrée principal — initialise l'UI et charge la sauvegarde.
- `starter.py`: Petite version de démonstration/POC montrant des entités et un combat simple.
- `save_player.json`: Fichier de sauvegarde contenant les données du joueur (chargé au démarrage, écrit à chaque changement important).

Gameplay
--------
- Menu principal : choisir entre aller au Château ou partir dans le Donjon.
- Donjon : rencontres aléatoires avec des monstres. Après la victoire, le joueur reçoit du butin :
  - Or (généré aléatoirement en fonction du niveau/puissance du monstre).
  - Chance d'obtenir une potion de soin.
- Combat : tour par tour entre le joueur et le monstre. Les dégâts sont calculés à partir des attributs du joueur (damage) et de l'armure (armor) de la cible.
- Mort du héros : si le joueur meurt, afficher un écran proposant de recommencer (réinitialiser état joueur) ou quitter le jeu.
- Fin de combat : le joueur peut retourner au Château via le menu de résultat.
- Château (shop) : panneau d'achat/vente d'armes et d'armures avec l'or gagné. Les achats et ventes sauvegardent immédiatement l'état du joueur.
- Inventaire : contient armes, armures et potions (pour l'instant seules les potions sont stockées mais l'architecture supporte armes/armures). Permet de boire une potion pour récupérer des PV.

Contrôles et raccourcis
-----------------------
- Flèches Haut/Bas : naviguer dans les menus et l'inventaire.
- Entrée : valider une sélection (acheter, vendre, utiliser).
- Esc : retour / fermer l'inventaire (raccourci global pour quitter un menu).
- e : équiper / déséquiper l'objet sélectionné (arme ou armure).
- p : boire une potion (si sélectionnée).
- Afficher "Retour" en bas du menu inventaire lorsque l'on peut revenir au menu précédent.

Système d'équipement et inventaire
----------------------------------
- Objets gérés : armes, armures, potions.
- Équiper / Déséquiper :
  - Touche `e` : équipe ou déséquipe l'arme/armure sélectionnée. Seule l'instance sélectionnée change d'état (éviter d'équiper/déséquiper en masse pour plusieurs objets identiques).
  - Touche `p` : boire une potion (consomme la potion et restaure des PV).
- Attributs du joueur :
  - `damage` : calculé comme base (2 si aucune arme équipée) + bonus de l'arme équipée.
  - `armor`  : calculé comme base (10 si aucune armure équipée) + bonus de l'armure équipée.
- Lorsqu'il y a plusieurs objets du même type (même nom/valeur), chaque objet doit avoir un identifiant unique interne (ou index) pour être distingué lors de l'équipement/déséquipement.

Magasin (Castle)
----------------
- Achat : sélectionner arme/armure disponible et l'acheter si vous avez assez d'or ; l'objet doit être ajouté à l'inventaire du joueur et l'or retiré.
- Vente : sélectionner un objet dans l'inventaire et le vendre contre de l'or (prix déterminé par l'objet).
- Sauvegarde : l'achat et la vente écrivent immédiatement la sauvegarde (`save_player.json`).
- Bug connu : dans l'implémentation actuelle, il est rapporté que les objets achetés ne s'ajoutent pas à l'inventaire — le comportement attendu est qu'ils apparaissent immédiatement dans l'inventaire et puissent être équipés. Vérifier que l'objet acheté est bien appendé à la liste d'inventaire et que la sauvegarde est déclenchée après l'opération.

Sauvegarde
----------
- Chargement : au lancement le jeu charge `save_player.json` s'il existe pour restaurer l'état du joueur.
- Sauvegarde automatique :
  - Après chaque achat/vente.
  - Lors du retour au Château (backup automatique).
  - Après événements importants (optionnellement à la fin de chaque combat).
- Format : JSON (structure lisible avec attributs du joueur, inventaire et or).

Notes de développement et debugging
----------------------------------
- "Enter to sell, Esc to return to Castle" : s'assurer que la touche Entrée est bien mappée à la fonction de vente et que la touche Esc déclenche la fermeture vers le Château.

Lancer le jeu
-------------
- Requis : Python 3 (la stdlib suffit dans la mesure où ncurses est utilisé via `curses` fourni par Python).
- Commande :
  - Sur macOS / Linux : `python3 main.py`
  - Sur Windows : utiliser WSL / adapter selon l'environnement (le module `curses` n'est pas natif sur Windows sans bibliothèques tierces).

FAQ / Erreurs connues
---------------------
Q: Les armes/armures achetées n'apparaissent pas dans l'inventaire.
R: Confirmer que la fonction d'achat appelle bien `player.inventory.append(obj)` et sauvegarde. Vérifier aussi que l'inventaire utilisé par le château et par l'écran d'inventaire référence la même instance `player`.

Contributions / Roadmap
-----------------------
- Ajouter UI pour afficher les détails d'un objet (statistiques).
- Étendre le loot (or, plusieurs types de potions, objets rares).
- Ajouter tests unitaires pour la logique d'équipement, shop et sauvegarde.

Licence
-------
Par défaut pas de licence spécifiée — ajoutez `LICENSE` si vous souhaitez une licence (p.ex. MIT).

