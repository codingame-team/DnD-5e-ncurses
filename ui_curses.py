import curses
import time
import copy
from typing import List
from entities import Entity, Player
from game import Game


MIN_COLS = 40
MIN_LINES = 10
SAVE_FILE = 'save_player.json'


class CursesUI:
	def __init__(self, stdscr, hero: Player, game: Game):
		self.stdscr = stdscr
		self.hero = hero
		# Keep a deep copy of the initial hero so we can restart
		self.hero_template = copy.deepcopy(hero)
		self.game = game

		# Two separate message systems
		self.exploration_log: List[str] = []  # Multi-line log for explore/combat modes
		self.panel_message: str = ""  # Single-line message for menus/panels
		self.panel_message_time: float = 0  # Time when panel message was set

		self.mode = 'main_menu'  # start at main menu
		self.current_monster = None
		self.inventory_cursor = 0
		self.menu_cursor = 0
		self.shop_cursor = 0
		self.sell_cursor = 0
		self.castle_menu_cursor = 0  # cursor pour le menu du château
		self.previous_mode = None  # mode précédent avant d'ouvrir l'inventaire

	def push_exploration(self, msg: str) -> None:
		"""Add message to exploration log (multi-line display)"""
		self.exploration_log.append(msg)
		# keep last 100 messages
		if len(self.exploration_log) > 100:
			self.exploration_log.pop(0)

	def push_panel(self, msg: str) -> None:
		"""Set panel message (single-line display, shown for 2 seconds)"""
		self.panel_message = msg
		self.panel_message_time = time.time()

	def get_panel_message(self) -> str:
		"""Get current panel message if still valid (within 2 seconds)"""
		if self.panel_message and time.time() - self.panel_message_time < 2:
			return self.panel_message
		return ""

	def restart(self) -> None:
		"""Restore hero to initial state and return to exploration."""
		self.hero = copy.deepcopy(self.hero_template)
		self.current_monster = None
		self.mode = 'explore'
		self.exploration_log.clear()
		self.push_exploration("You are revived. Press 'w' to continue wandering.")

	def open_inventory(self) -> None:
		self.previous_mode = self.mode  # Sauvegarder le mode actuel
		self.inventory_cursor = 0
		self.mode = 'inventory'
		# Ne pas effacer les messages pour que les push soient visibles
		# self.log.clear()  # REMOVED to keep messages visible
		try:
			self.stdscr.erase()
			self.stdscr.refresh()
		except Exception:
			pass

	def close_inventory(self) -> None:
		# Ne pas effacer les messages pour qu'ils restent visibles
		# self.log.clear()  # REMOVED to keep messages visible
		# Retourner au mode précédent (ou explore par défaut)
		self.mode = self.previous_mode if self.previous_mode else 'explore'
		self.previous_mode = None  # Réinitialiser
		try:
			self.stdscr.erase()
			self.stdscr.refresh()
		except Exception:
			pass

	def draw_inventory(self, lines: int, cols: int) -> None:
		self.check_bounds()
		try:
			# Draw inventory centered
			title = "Inventory"
			self.stdscr.addstr(1, 0, title, curses.A_UNDERLINE)

			# Gold display
			self.stdscr.addstr(2, 0, f"Gold: {self.hero.gold}")

			# Potions
			pots = self.hero.list_potions()
			self.stdscr.addstr(4, 0, "Potions:")
			start_idx = 0
			if not pots:
				self.stdscr.addstr(5, 2, "(none)")
				start_idx = 0
			else:
				for idx, p in enumerate(pots):
					marker = '>' if self.inventory_cursor == idx else ' '
					self.stdscr.addstr(5 + idx, 2, f"{marker} {p.name} (+{p.heal} HP)")
				start_idx = len(pots)

			# Weapons
			wep_start = 7 + max(0, len(pots))
			self.stdscr.addstr(wep_start, 0, "Weapons:")
			for i, w in enumerate(self.hero.weapons):
				idx = start_idx + i
				marker = '>' if self.inventory_cursor == idx else ' '
				equip_mark = '(E)' if self.hero.equipped_weapon == w else '   '
				self.stdscr.addstr(wep_start + 1 + i, 2, f"{marker} {w.name} {equip_mark} (DMG+{w.damage})")
			wep_count = len(self.hero.weapons)

			# Armors
			arm_start = wep_start + 2 + max(0, wep_count)
			self.stdscr.addstr(arm_start, 0, "Armors:")
			for j, a in enumerate(self.hero.armors):
				idx = start_idx + wep_count + j
				marker = '>' if self.inventory_cursor == idx else ' '
				equip_mark = '(E)' if self.hero.equipped_armor == a else '   '
				self.stdscr.addstr(arm_start + 1 + j, 2, f"{marker} {a.name} {equip_mark} (ARM {a.value})")
			arm_count = len(self.hero.armors)

			# Footer with separator line
			separator_line = lines - 4
			if separator_line > arm_start + arm_count + 2:
				self.stdscr.addstr(separator_line, 0, "─" * min(cols - 1, 60))

			# Special line for pushed messages (always visible)
			message_line = lines - 3
			panel_msg = self.get_panel_message()
			if panel_msg:
				# Display message in highlighted style
				self.stdscr.addstr(message_line, 0, ">>> " + panel_msg[:cols-5], curses.A_BOLD)
			else:
				# Display empty space to keep layout consistent
				self.stdscr.addstr(message_line, 0, "")

			# Instructions line
			self.stdscr.addstr(lines-2, 0, "[u] Use item  [e] Equip/Unequip  [Esc] Return to previous panel", curses.A_REVERSE)

		except curses.error:
			# Window resized during drawing - will retry on next frame
			pass

	def try_drink_selected(self) -> None:
		"""Legacy method - kept for backward compatibility but unused"""
		pots = self.hero.list_potions()
		if not pots:
			self.push_panel("You have no potions.")
			return
		idx = self.inventory_cursor
		healed = self.hero.drink_potion(idx)
		if healed is None:
			self.push_panel("Invalid selection.")
		else:
			self.push_panel(f"You drink {pots[idx].name} and recover {healed} HP.")

	def draw_main_menu(self, lines: int, cols: int) -> None:
		self.check_bounds()
		try:
			options = ['Go to Dungeon', 'Go to Castle', 'Quit']
			self.stdscr.addstr(2, 0, "Main Menu", curses.A_UNDERLINE)
			for idx, opt in enumerate(options):
				marker = '>' if idx == self.menu_cursor else ' '
				self.stdscr.addstr(4 + idx, 0, f"{marker} {opt}")
			# Special line for pushed messages
			self.stdscr.addstr(lines-3, 0, self.get_panel_message())
			self.stdscr.addstr(lines-2, 0, "Use arrows or j/k to move — Enter to select", curses.A_BOLD)
		except curses.error:
			# Window resized during drawing - will retry on next frame
			pass

	def draw_castle_menu(self, lines: int, cols: int) -> None:
		self.check_bounds()
		try:
			self.stdscr.addstr(1, 0, "Castle", curses.A_UNDERLINE)
			self.stdscr.addstr(3, 0, f"Gold: {self.hero.gold}")

			options = ['Buy Items', 'Sell Items', 'Inventory', 'Return to Main Menu']
			self.stdscr.addstr(5, 0, "What would you like to do?")
			for idx, opt in enumerate(options):
				marker = '>' if idx == self.castle_menu_cursor else ' '
				self.stdscr.addstr(7 + idx, 0, f"{marker} {opt}")

			# Special line for pushed messages
			self.stdscr.addstr(lines-3, 0, self.get_panel_message())
			self.stdscr.addstr(lines-2, 0, "Use arrows or j/k to move — Enter to select — Esc to return", curses.A_BOLD)
		except curses.error:
			# Window resized during drawing - will retry on next frame
			pass

	def draw_buy_menu(self, lines: int, cols: int) -> None:
		self.check_bounds()
		try:
			self.stdscr.addstr(1, 0, "Castle - Shop (Buy)", curses.A_UNDERLINE)
			self.stdscr.addstr(3, 0, f"Gold: {self.hero.gold}")
			weps = self.game.get_shop_weapons()
			arms = self.game.get_shop_armors()
			self.stdscr.addstr(5, 0, "Weapons:")
			for i, w in enumerate(weps):
				marker = '>' if self.shop_cursor == i else ' '
				self.stdscr.addstr(6 + i, 0, f"{marker} {w.name} (DMG+{w.damage}) cost:{w.cost}")
			base = 10 + len(weps)
			self.stdscr.addstr(base, 0, "Armors:")
			for j, a in enumerate(arms):
				marker = '>' if self.shop_cursor == (len(weps) + j) else ' '
				self.stdscr.addstr(base + 1 + j, 0, f"{marker} {a.name} (ARM {a.value}) cost:{a.cost}")
			# Special line for pushed messages
			self.stdscr.addstr(lines-4, 0, self.get_panel_message())
			# shop actions
			self.stdscr.addstr(lines-2, 0, "Arrow keys/jk to navigate — Enter to select — Esc to return", curses.A_BOLD)
		except curses.error:
			# Window resized during drawing - will retry on next frame
			pass

	def draw_sell_menu(self, lines: int, cols: int) -> None:
		self.check_bounds()
		try:
			self.stdscr.addstr(1, 0, "Castle - Sell Items", curses.A_UNDERLINE)
			self.stdscr.addstr(3, 0, f"Gold: {self.hero.gold}")
			self.stdscr.addstr(5, 0, "Weapons:")
			for i, w in enumerate(self.hero.weapons):
				marker = '>' if self.sell_cursor == i else ' '
				self.stdscr.addstr(6 + i, 0, f"{marker} {w.name} (DMG+{w.damage}) sell:{w.cost//2}")
			base = 10 + len(self.hero.weapons) + 2
			self.stdscr.addstr(base, 0, "Armors:")
			# weapons then armors: mark selected by sell_cursor (combined index)
			for j, a in enumerate(self.hero.armors):
				marker = '>' if self.sell_cursor == (len(self.hero.weapons) + j) else ' '
				self.stdscr.addstr(base + 1 + j, 0, f"{marker} {a.name} (ARM {a.value}) sell:{a.cost // 2}")
			# Special line for pushed messages
			self.stdscr.addstr(lines-3, 0, self.get_panel_message())
			self.stdscr.addstr(lines-2, 0, "Enter to sell — Esc to return to Castle menu", curses.A_BOLD)
		except curses.error:
			# Window resized during drawing - will retry on next frame
			pass

	def draw(self) -> None:
		self.stdscr.erase()
		lines, cols = self.stdscr.getmaxyx()
		self.check_bounds()
		# If main menu
		if self.mode == 'main_menu':
			self.draw_main_menu(lines, cols)
			self.stdscr.refresh()
			return
		# If in castle menu
		if self.mode == 'castle_menu':
			self.draw_castle_menu(lines, cols)
			self.stdscr.refresh()
			return
		# If in castle shop
		if self.mode == 'castle_shop':
			self.draw_buy_menu(lines, cols)
			self.stdscr.refresh()
			return
		# If selling
		if self.mode == 'sell':
			self.draw_sell_menu(lines, cols)
			self.stdscr.refresh()
			return
		# If in inventory mode, draw it and return early (BEFORE exploration log)
		if self.mode == 'inventory':
			self.draw_inventory(lines, cols)
			self.stdscr.refresh()
			return

		try:
			# Status bar (top) - show effective stats
			status = f"{self.hero.name} — HP: {self.hero.hp}/{self.hero.max_hp}  DMG: {self.hero.damage}  ARM: {self.hero.armor_class}  Gold: {self.hero.gold}"
			self.stdscr.addstr(0, 0, status, curses.A_REVERSE)

			# Exploration log window (multi-line for explore/combat modes ONLY)
			log_h = lines - 6
			start = max(0, len(self.exploration_log) - log_h)
			for idx, msg in enumerate(self.exploration_log[start:]):
				self.stdscr.addstr(1 + idx, 0, msg[:cols-1])

			# Prompt
			if self.mode == 'dead':
				prompt = "[r] Restart  [q] Quit"
			elif self.mode == 'explore':
				prompt = "[w] Wander  [i] Inventory  [m] Menu  [h] Help"
			else:
				prompt = "[a] Attack  [r] Flee  [i] Inventory"
			self.stdscr.addstr(lines-2, 0, prompt, curses.A_BOLD)
		except curses.error:
			# Window resized during drawing - will retry on next frame
			pass
		self.stdscr.refresh()

	def animate_encounter(self, text: str) -> None:
		# simple flash animation
		for i in range(4):
			attr = curses.A_BLINK if i % 2 == 0 else curses.A_BOLD
			self.stdscr.addstr(0, 0, text.center(40), attr)
			self.stdscr.refresh()
			time.sleep(0.15)

	def check_bounds(self):
		lines, cols = self.stdscr.getmaxyx()
		while cols < MIN_COLS or lines < MIN_LINES:
			try:
				self.stdscr.erase()
				self.stdscr.addstr(0, 0, "Terminal too small. Resize to continue.")
				self.stdscr.refresh()
			except curses.error:
				# Window too small even for error message
				pass
			time.sleep(0.5)  # wait before checking again
			lines, cols = self.stdscr.getmaxyx()

	def mainloop(self) -> None:
		"""Main game loop following Single Responsibility Principle"""
		self.stdscr.nodelay(False)
		curses.curs_set(0)
		self.push_exploration("Welcome to the dungeon. Press 'w' to wander.")

		while True:
			self.check_bounds()
			self.draw()
			c = self.stdscr.getch()

			# Dispatch to appropriate handler based on mode (Open/Closed Principle)
			if self.mode == 'main_menu':
				if not self._handle_main_menu(c):
					break  # User chose to quit
			elif self.mode == 'castle_menu':
				self._handle_castle_menu(c)
			elif self.mode == 'castle_shop':
				self._handle_castle_shop(c)
			elif self.mode == 'sell':
				self._handle_sell_mode(c)
			elif self.mode == 'dead':
				if not self._handle_dead_mode(c):
					break  # User chose to quit
			elif self.mode == 'inventory':
				self._handle_inventory_mode(c)
			elif self.mode == 'explore':
				self._handle_explore_mode(c)
			elif self.mode == 'combat':
				self._handle_combat_mode(c)

	def _handle_main_menu(self, c: int) -> bool:
		"""Handle main menu input. Returns False if user wants to quit."""
		if c in (curses.KEY_DOWN, ord('j')):
			self.menu_cursor = min(self.menu_cursor + 1, 2)
		elif c in (curses.KEY_UP, ord('k')):
			self.menu_cursor = max(0, self.menu_cursor - 1)
		elif c in (ord('\n'), ord('\r')):
			if self.menu_cursor == 0:
				# go to dungeon
				self.mode = 'explore'
				self.push_exploration('You head into the dungeon...')
			elif self.menu_cursor == 1:
				# Save player backup when entering the Castle
				try:
					self.hero.save_to_file(SAVE_FILE)
				except Exception:
					pass
				self.mode = 'castle_menu'
				self.castle_menu_cursor = 0
			else:
				return False  # Quit
		elif c == ord('q'):
			return False  # Quit
		return True  # Continue

	def _handle_castle_menu(self, c: int) -> None:
		"""Handle castle menu input."""
		if c in (curses.KEY_DOWN, ord('j')):
			self.castle_menu_cursor = min(self.castle_menu_cursor + 1, 3)
		elif c in (curses.KEY_UP, ord('k')):
			self.castle_menu_cursor = max(0, self.castle_menu_cursor - 1)
		elif c in (ord('\n'), ord('\r')):
			if self.castle_menu_cursor == 0:
				# Go to Buy
				self.mode = 'castle_shop'
				self.shop_cursor = 0
			elif self.castle_menu_cursor == 1:
				# Go to Sell
				self.mode = 'sell'
				self.sell_cursor = 0
			elif self.castle_menu_cursor == 2:
				# Go to Inventory
				self.open_inventory()
			else:
				# Return to Main Menu
				self.mode = 'main_menu'
				self.menu_cursor = 0
		elif c == 27:  # Esc - return to main menu
			self.mode = 'main_menu'
			self.menu_cursor = 0

	def _handle_castle_shop(self, c: int) -> None:
		"""Handle castle shop input."""
		weps = self.game.get_shop_weapons()
		arms = self.game.get_shop_armors()
		total_items = len(weps) + len(arms)

		if c in (curses.KEY_DOWN, ord('j')):
			self.shop_cursor = (self.shop_cursor + 1) % max(1, total_items)
		elif c in (curses.KEY_UP, ord('k')):
			self.shop_cursor = (self.shop_cursor - 1) % max(1, total_items)
		elif c in (ord('\n'), ord('\r')):
			self._buy_item(weps, arms)
		elif c == ord('i'):
			self.open_inventory()
		elif c == 27:  # Esc - return to castle menu
			self.mode = 'castle_menu'
			self.castle_menu_cursor = 0

	def _buy_item(self, weps, arms) -> None:
		"""Buy selected item (Dependency Inversion - depends on abstractions)."""
		if self.shop_cursor < len(weps):
			item = weps[self.shop_cursor]
			if self.hero.spend_gold(item.cost):
				try:
					import copy as _copy
					self.hero.add_weapon(_copy.deepcopy(item))
				except Exception:
					self.hero.add_weapon(item)
				self.push_panel(f"You bought {item.name}.")
				try:
					self.hero.save_to_file(SAVE_FILE)
				except Exception:
					pass
			else:
				self.push_panel("Not enough gold.")
		else:
			idx = self.shop_cursor - len(weps)
			item = arms[idx]
			if self.hero.spend_gold(item.cost):
				try:
					import copy as _copy
					self.hero.add_armor(_copy.deepcopy(item))
				except Exception:
					self.hero.add_armor(item)
				self.push_panel(f"You bought {item.name}.")
				try:
					self.hero.save_to_file(SAVE_FILE)
				except Exception:
					pass
			else:
				self.push_panel("Not enough gold.")

	def _handle_sell_mode(self, c: int) -> None:
		"""Handle sell mode input."""
		total_sell = len(self.hero.weapons) + len(self.hero.armors)

		if c in (curses.KEY_DOWN, ord('j')):
			self.sell_cursor = (self.sell_cursor + 1) % max(1, total_sell)
		elif c in (curses.KEY_UP, ord('k')):
			self.sell_cursor = (self.sell_cursor - 1) % max(1, total_sell)
		elif c in (ord('\n'), ord('\r')):
			self._sell_item()
		elif c == 27:  # Esc - return to castle menu
			self.mode = 'castle_menu'
			self.castle_menu_cursor = 0

	def _sell_item(self) -> None:
		"""Sell selected item."""
		if self.sell_cursor < len(self.hero.weapons):
			val = self.hero.sell_weapon(self.sell_cursor)
			if val:
				self.push_panel(f"Sold weapon for {val} gold.")
				try:
					self.hero.save_to_file(SAVE_FILE)
				except Exception:
					pass
			else:
				self.push_panel("Nothing to sell.")
		else:
			idx = self.sell_cursor - len(self.hero.weapons)
			val = self.hero.sell_armor(idx)
			if val:
				self.push_panel(f"Sold armor for {val} gold.")
				try:
					self.hero.save_to_file(SAVE_FILE)
				except Exception:
					pass
			else:
				self.push_panel("Nothing to sell.")

	def _handle_dead_mode(self, c: int) -> bool:
		"""Handle dead mode input. Returns False if user wants to quit."""
		if c == ord('r'):
			self.restart()
		elif c == ord('q'):
			return False  # Quit
		return True  # Continue

	def _handle_inventory_mode(self, c: int) -> None:
		"""Handle inventory mode input."""
		if c in (curses.KEY_DOWN, ord('j')):
			total = len(self.hero.inventory) + len(self.hero.weapons) + len(self.hero.armors)
			if total > 0:
				self.inventory_cursor = (self.inventory_cursor + 1) % total
		elif c in (curses.KEY_UP, ord('k')):
			total = len(self.hero.inventory) + len(self.hero.weapons) + len(self.hero.armors)
			if total > 0:
				self.inventory_cursor = (self.inventory_cursor - 1) % total
		elif c == ord('u'):
			self._use_item()
		elif c == ord('e'):
			self._equip_item()
		elif c in (ord('i'), 27):  # 'i' or ESC key
			self.close_inventory()

	def _use_item(self) -> None:
		"""Use selected item (only potions)."""
		if self.inventory_cursor < len(self.hero.inventory):
			healed = self.hero.drink_potion(self.inventory_cursor)
			if healed is None:
				self.push_panel("Invalid selection.")
			else:
				self.push_panel(f"You drink a potion and recover {healed} HP.")
			try:
				self.hero.save_to_file(SAVE_FILE)
			except Exception:
				pass
		else:
			self.push_panel("Cannot use this item. Only potions can be used.")

	def _equip_item(self) -> None:
		"""Equip/unequip selected item (weapons and armors)."""
		inv_len = len(self.hero.inventory)
		wep_len = len(self.hero.weapons)

		if self.inventory_cursor < inv_len:
			self.push_panel("Cannot equip a potion. Use 'u' to drink.")
		elif self.inventory_cursor < inv_len + wep_len:
			# weapon slot
			idx = self.inventory_cursor - inv_len
			w = self.hero.weapons[idx]
			if self.hero.equipped_weapon is w:
				self.hero.unequip_weapon()
				self.push_panel(f"You unequipped {w.name}.")
			else:
				self.hero.equip_weapon(idx)
				self.push_panel(f"You equipped {w.name}.")
			try:
				self.hero.save_to_file(SAVE_FILE)
			except Exception:
				pass
		else:
			# armor slot
			idx = self.inventory_cursor - inv_len - wep_len
			a = self.hero.armors[idx]
			if self.hero.equipped_armor is a:
				self.hero.unequip_armor()
				self.push_panel(f"You unequipped {a.name}.")
			else:
				self.hero.equip_armor(idx)
				self.push_panel(f"You equipped {a.name}.")
			try:
				self.hero.save_to_file(SAVE_FILE)
			except Exception:
				pass

	def _handle_explore_mode(self, c: int) -> None:
		"""Handle explore mode input."""
		if c == ord('w'):
			msg, monster = self.game.wander(self.hero)
			self.push_exploration(msg)
			if monster:
				self.current_monster = monster
				self.mode = 'combat'
				self.animate_encounter(f"!! {monster.name.upper()} ENCOUNTER !!")
		elif c == ord('h'):
			self.push_exploration("Controls: w-wander, q-quit, h-help")
		elif c == ord('i'):
			self.open_inventory()
		elif c == ord('m'):
			self.mode = 'main_menu'
			self.menu_cursor = 0

	def _handle_combat_mode(self, c: int) -> None:
		"""Handle combat mode input."""
		if c == ord('a'):
			self._attack_monster()
		elif c == ord('r'):
			self._attempt_flee()
		elif c == ord('i'):
			self.open_inventory()

	def _attack_monster(self) -> None:
		"""Attack the current monster."""
		d = self.game.attack(self.hero, self.current_monster)
		if d > 0:
			self.push_exploration(f"You hit {self.current_monster.name} for {d} damage.")
		else:
			self.push_exploration("You miss!")

		if not self.current_monster.is_alive():
			self._handle_monster_defeated()
			return

		# Monster's turn
		self._monster_attack()

	def _handle_monster_defeated(self) -> None:
		"""Handle monster defeat and loot."""
		self.push_exploration(f"{self.current_monster.name} has been defeated!")

		# Handle loot
		p = self.game.handle_loot(self.current_monster)
		if p:
			self.hero.add_potion(p)
			self.push_exploration(f"You found a {p.name}!")

		# Award gold
		gold = self.game.gold_reward(self.current_monster)
		if gold > 0:
			self.hero.add_gold(gold)
			self.push_exploration(f"You gained {gold} gold.")
			self.push_exploration("Open the main menu with 'm' to return to the Castle.")

		self.mode = 'explore'
		self.current_monster = None

	def _monster_attack(self) -> None:
		"""Monster attacks the player."""
		md = self.game.attack(self.current_monster, self.hero)
		if md > 0:
			self.push_exploration(f"{self.current_monster.name} hits you for {md} damage.")
		else:
			self.push_exploration(f"{self.current_monster.name} misses!")

		if not self.hero.is_alive():
			self.push_exploration("You have been slain! Game over.")
			self.push_exploration("Press 'r' to restart or 'q' to quit.")
			self.mode = 'dead'
			self.current_monster = None

	def _attempt_flee(self) -> None:
		"""Attempt to flee from combat."""
		if self.game.attempt_flee(self.hero, self.current_monster):
			self.push_exploration("You fled successfully.")
			self.mode = 'explore'
			self.current_monster = None
		else:
			self.push_exploration("Flee failed!")
			self._monster_attack()  # Monster gets a free attack


def run_curses(hero: Entity):
	game = Game()
	def _wrapped(stdscr):
		ui = CursesUI(stdscr, hero, game)
		ui.mainloop()

	curses.wrapper(_wrapped)
