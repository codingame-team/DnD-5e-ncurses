from entities import Entity, Player
from ui_curses import run_curses

SAVE_FILE = 'save_player.json'


if __name__ == '__main__':
	# Try to load saved player
	player = Player.load_from_file(SAVE_FILE)
	if player is None:
		# No save found: create default player
		player = Player(name='Hero', hp=20, max_hp=30, gold=30)
	else:
		print(f"Loaded saved player: {player.name} (Gold: {player.gold})")

	run_curses(player)
