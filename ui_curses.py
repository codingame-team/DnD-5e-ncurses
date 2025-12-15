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
		self.log: List[str] = []
		self.mode = 'main_menu'  # start at main menu
		self.current_monster = None
		self.inventory_cursor = 0
		self.menu_cursor = 0
		self.shop_cursor = 0
		self.sell_cursor = 0

	def push(self, msg: str) -> None:
		self.log.append(msg)
		# keep last 100 messages
		if len(self.log) > 100:
			self.log.pop(0)

	def restart(self) -> None:
		"""Restore hero to initial state and return to exploration."""
		self.hero = copy.deepcopy(self.hero_template)
		self.current_monster = None
		self.mode = 'explore'
		self.log.clear()
		self.push("You are revived. Press 'w' to continue wandering.")

	def open_inventory(self) -> None:
		self.inventory_cursor = 0
		self.mode = 'inventory'
		# clear previous messages when entering inventory to present a fresh view
		self.log.clear()
		try:
			self.stdscr.erase()
			self.stdscr.refresh()
		except Exception:
			pass

	def close_inventory(self) -> None:
		# clear messages when leaving inventory to reduce clutter
		self.log.clear()
		self.mode = 'explore'
		try:
			self.stdscr.erase()
			self.stdscr.refresh()
		except Exception:
			pass

	def draw_inventory(self, lines: int, cols: int) -> None:
		# Draw inventory centered
		title = "Inventory"
		self.stdscr.addstr(1, 0, title, curses.A_UNDERLINE)
		# Potions
		pots = self.hero.list_potions()
		self.stdscr.addstr(3, 0, "Potions:")
		start_idx = 0
		if not pots:
			self.stdscr.addstr(4, 2, "(none)")
			start_idx = 0
		else:
			for idx, p in enumerate(pots):
				marker = '>' if self.inventory_cursor == idx else ' '
				self.stdscr.addstr(4 + idx, 2, f"{marker} {p.name} (+{p.heal} HP)")
			start_idx = len(pots)

		# Weapons
		wep_start = 6 + max(0, len(pots))
		self.stdscr.addstr(wep_start, 0, "Weapons:")
		for i, w in enumerate(self.hero.weapons):
			idx = start_idx + i
			marker = '>' if self.inventory_cursor == idx else ' '
			equip_mark = '(E)' if self.hero.equipped_weapon is w else '   '
			self.stdscr.addstr(wep_start + 1 + i, 2, f"{marker} {w.name} {equip_mark} (DMG+{w.damage})")
		wep_count = len(self.hero.weapons)

		# Armors
		arm_start = wep_start + 2 + max(0, wep_count)
		self.stdscr.addstr(arm_start, 0, "Armors:")
		for j, a in enumerate(self.hero.armors):
			idx = start_idx + wep_count + j
			marker = '>' if self.inventory_cursor == idx else ' '
			equip_mark = '(E)' if self.hero.equipped_armor is a else '   '
			self.stdscr.addstr(arm_start + 1 + j, 2, f"{marker} {a.name} {equip_mark} (ARM {a.value})")
		arm_count = len(self.hero.armors)

		# Footer
		self.stdscr.addstr(lines-4, 0, "Use arrows/jk to move. 'p' to drink potion, 'e' to equip/unequip.")
		self.stdscr.addstr(lines-2, 0, "Press 'i' or Esc to return to the game.", curses.A_BOLD)

	def try_drink_selected(self) -> None:
		pots = self.hero.list_potions()
		if not pots:
			self.push("You have no potions.")
			return
		idx = self.inventory_cursor
		healed = self.hero.drink_potion(idx)
		if healed is None:
			self.push("Invalid selection.")
		else:
			self.push(f"You drink {pots[idx].name} and recover {healed} HP.")

	def draw_main_menu(self, lines: int, cols: int) -> None:
		options = ['Go to Dungeon', 'Go to Castle', 'Quit']
		self.stdscr.addstr(2, 0, "Main Menu", curses.A_UNDERLINE)
		for idx, opt in enumerate(options):
			marker = '>' if idx == self.menu_cursor else ' '
			self.stdscr.addstr(4 + idx, 0, f"{marker} {opt}")
		self.stdscr.addstr(lines-2, 0, "Use arrows or j/k to move — Enter to select", curses.A_BOLD)

	def draw_castle(self, lines: int, cols: int) -> None:
		self.stdscr.addstr(1, 0, "Castle - Shop", curses.A_UNDERLINE)
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
		# shop actions
		self.stdscr.addstr(lines-3, 0, "[b] Buy item  [s] Sell items  [i] Inventory  [m] Main Menu")
		self.stdscr.addstr(lines-2, 0, "Arrow keys/jk to navigate, Enter to buy, Esc to return", curses.A_BOLD)

	def draw_sell_menu(self, lines: int, cols: int) -> None:
		self.stdscr.addstr(1, 0, "Sell Items", curses.A_UNDERLINE)
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
		self.stdscr.addstr(lines-2, 0, "Enter to sell, Esc to return to Castle", curses.A_BOLD)

	def draw(self) -> None:
		self.stdscr.erase()
		lines, cols = self.stdscr.getmaxyx()
		if cols < MIN_COLS or lines < MIN_LINES:
			self.stdscr.addstr(0, 0, "Terminal too small. Resize to continue.")
			self.stdscr.refresh()
			return
		# If main menu
		if self.mode == 'main_menu':
			self.draw_main_menu(lines, cols)
			self.stdscr.refresh()
			return
		# If in castle
		if self.mode == 'castle':
			self.draw_castle(lines, cols)
			self.stdscr.refresh()
			return
		# If selling
		if self.mode == 'sell':
			self.draw_sell_menu(lines, cols)
			self.stdscr.refresh()
			return
		# Status bar (top) - show effective stats
		status = f"{self.hero.name} — HP: {self.hero.hp}/{self.hero.max_hp}  DMG: {self.hero.damage}  ARM: {self.hero.armor_class}  Gold: {self.hero.gold}"
		self.stdscr.addstr(0, 0, status, curses.A_REVERSE)

		# Log window
		log_h = lines - 6
		start = max(0, len(self.log) - log_h)
		for idx, msg in enumerate(self.log[start:]):
			self.stdscr.addstr(1 + idx, 0, msg[:cols-1])

		# If in inventory mode, draw it and return early
		if self.mode == 'inventory':
			self.draw_inventory(lines, cols)
			self.stdscr.refresh()
			return

		# Prompt
		if self.mode == 'dead':
			prompt = "[r] Restart  [q] Quit"
		elif self.mode == 'explore':
			prompt = "[w] Wander  [i] Inventory  [m] Menu  [q] Quit  [h] Help"
		else:
			prompt = "[a] Attack  [r] Flee  [i] Inventory  [m] Menu  [q] Quit"
		self.stdscr.addstr(lines-2, 0, prompt, curses.A_BOLD)
		self.stdscr.refresh()

	def animate_encounter(self, text: str) -> None:
		# simple flash animation
		for i in range(4):
			attr = curses.A_BLINK if i % 2 == 0 else curses.A_BOLD
			self.stdscr.addstr(0, 0, text.center(40), attr)
			self.stdscr.refresh()
			time.sleep(0.15)

	def mainloop(self) -> None:
		self.stdscr.nodelay(False)
		curses.curs_set(0)
		self.push("Welcome to the dungeon. Press 'w' to wander.")
		while True:
			self.draw()
			c = self.stdscr.getch()
			# Global main menu handling
			if self.mode == 'main_menu':
				if c in (curses.KEY_DOWN, ord('j')):
					self.menu_cursor = min(self.menu_cursor + 1, 2)
				elif c in (curses.KEY_UP, ord('k')):
					self.menu_cursor = max(0, self.menu_cursor - 1)
				elif c in (ord('\n'), ord('\r')):
					if self.menu_cursor == 0:
						# go to dungeon
						self.mode = 'explore'
						self.push('You head into the dungeon...')
						continue
					elif self.menu_cursor == 1:
						# Save player backup when entering the Castle
						try:
							self.hero.save_to_file(SAVE_FILE)
						except Exception:
							pass
						self.mode = 'castle'
						continue
					else:
						break
				elif c == ord('q'):
					break
				continue
			# Castle mode handling
			if self.mode == 'castle':
				weps = self.game.get_shop_weapons()
				arms = self.game.get_shop_armors()
				# combined navigation: weapons then armors
				total_items = len(weps) + len(arms)
				if c in (curses.KEY_DOWN, ord('j')):
					self.shop_cursor = (self.shop_cursor + 1) % max(1, total_items)
				elif c in (curses.KEY_UP, ord('k')):
					self.shop_cursor = (self.shop_cursor - 1) % max(1, total_items)
				elif c in (ord('\n'), ord('\r'), ord('b')):
					# Buy selected: if cursor in weapons range -> weapon else armor
					if self.shop_cursor < len(weps):
						item = weps[self.shop_cursor]
						if self.hero.spend_gold(item.cost):
							try:
								import copy as _copy
								self.hero.add_weapon(_copy.deepcopy(item))
							except Exception:
								self.hero.add_weapon(item)
							self.push(f"You bought {item.name}.")
							try:
								self.hero.save_to_file(SAVE_FILE)
							except Exception:
								pass
						else:
							self.push("Not enough gold.")
					else:
						idx = self.shop_cursor - len(weps)
						item = arms[idx]
						if self.hero.spend_gold(item.cost):
							try:
								import copy as _copy
								self.hero.add_armor(_copy.deepcopy(item))
							except Exception:
								self.hero.add_armor(item)
							self.push(f"You bought {item.name}.")
							try:
								self.hero.save_to_file(SAVE_FILE)
							except Exception:
								pass
						else:
							self.push("Not enough gold.")
				elif c == ord('s'):
					self.mode = 'sell'
					self.sell_cursor = 0
					continue
				elif c == ord('i'):
					self.open_inventory()
					continue
				elif c == ord('m'):
					self.mode = 'main_menu'
					self.menu_cursor = 0
					# if returning to main menu from somewhere else there is no save here; castle save happens when entering castle
					continue
				elif c == 27:  # Esc
					self.mode = 'main_menu'
					self.menu_cursor = 0
					continue
				continue
			# Sell mode
			if self.mode == 'sell':
				# combine weapons and armors into a single list for selling
				total_sell = len(self.hero.weapons) + len(self.hero.armors)
				if c in (curses.KEY_DOWN, ord('j')):
					self.sell_cursor = (self.sell_cursor + 1) % max(1, total_sell)
				elif c in (curses.KEY_UP, ord('k')):
					self.sell_cursor = (self.sell_cursor - 1) % max(1, total_sell)
				elif c in (ord('\n'), ord('\r')):
					if self.sell_cursor < len(self.hero.weapons):
						val = self.hero.sell_weapon(self.sell_cursor)
						if val:
							self.push(f"Sold weapon for {val} gold.")
							# save after selling
							try:
								self.hero.save_to_file(SAVE_FILE)
							except Exception:
								pass
						else:
							self.push("Nothing to sell.")
					else:
						idx = self.sell_cursor - len(self.hero.weapons)
						val = self.hero.sell_armor(idx)
						if val:
							self.push(f"Sold armor for {val} gold.")
							# save after selling
							try:
								self.hero.save_to_file(SAVE_FILE)
							except Exception:
								pass
						else:
							self.push("Nothing to sell.")
				elif c in (27, ord('m'), ord('b')):
					# Esc or 'm' or 'b' to return to castle
					self.mode = 'castle'
					continue
				continue
			# If player is dead, allow restart or quit
			if self.mode == 'dead':
				if c == ord('r'):
					self.restart()
					continue
				elif c == ord('q'):
					break
				else:
					continue
			if self.mode == 'inventory':
				# navigation
				if c in (curses.KEY_DOWN, ord('j')):
					# compute total items
					total = len(self.hero.inventory) + len(self.hero.weapons) + len(self.hero.armors)
					if total > 0:
						self.inventory_cursor = (self.inventory_cursor + 1) % total
				elif c in (curses.KEY_UP, ord('k')):
					total = len(self.hero.inventory) + len(self.hero.weapons) + len(self.hero.armors)
					if total > 0:
						self.inventory_cursor = (self.inventory_cursor - 1) % total
				elif c == ord('p'):
					# drink potion if cursor on potion
					if self.inventory_cursor < len(self.hero.inventory):
						healed = self.hero.drink_potion(self.inventory_cursor)
						if healed is None:
							self.push("Invalid selection.")
						else:
							self.push(f"You drink a potion and recover {healed} HP.")
						# save after potion use
						try:
							self.hero.save_to_file(SAVE_FILE)
						except Exception:
							pass
					else:
						self.push("No potion selected.")
				elif c == ord('e'):
					# equip/unequip based on cursor position
					inv_len = len(self.hero.inventory)
					wep_len = len(self.hero.weapons)
					if self.inventory_cursor < inv_len:
						self.push("Cannot equip a potion. Use 'p' to drink.")
					elif self.inventory_cursor < inv_len + wep_len:
						# weapon slot
						idx = self.inventory_cursor - inv_len
						w = self.hero.weapons[idx]
						if self.hero.equipped_weapon is w:
							self.hero.unequip_weapon()
							self.push(f"You unequipped {w.name}.")
						else:
							self.hero.equip_weapon(idx)
							self.push(f"You equipped {w.name}.")
						# save
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
							self.push(f"You unequipped {a.name}.")
						else:
							self.hero.equip_armor(idx)
							self.push(f"You equipped {a.name}.")
						# save
						try:
							self.hero.save_to_file(SAVE_FILE)
						except Exception:
							pass
				elif c in (ord('\n'), ord('\r'), ord('b')):
					# store name before drinking because drink_potion pops it
					pots = self.hero.list_potions()
					if pots and self.inventory_cursor < len(pots):
						pname = pots[self.inventory_cursor].name
						healed = self.hero.drink_potion(self.inventory_cursor)
						if healed is not None:
							self.push(f"You drink {pname} and recover {healed} HP.")
							try:
								self.hero.save_to_file(SAVE_FILE)
							except Exception:
								pass
						else:
							self.push("Invalid selection.")
					else:
						self.push("You have no potions or cursor not on potion.")
				elif c == ord('i'):
					self.close_inventory()
				elif c == 27:  # ESC key
					self.close_inventory()
				continue
			if self.mode == 'explore':
				if c == ord('w'):
					msg, monster = self.game.wander(self.hero)
					self.push(msg)
					if monster:
						self.current_monster = monster
						self.mode = 'combat'
						self.animate_encounter(f"!! {monster.name.upper()} ENCOUNTER !!")
				elif c == ord('h'):
					self.push("Controls: w-wander, q-quit, h-help")
				elif c == ord('i'):
					self.open_inventory()
				elif c == ord('m'):
					self.mode = 'main_menu'
					self.menu_cursor = 0
			else:  # combat
				if c == ord('a'):
					d = self.game.attack(self.hero, self.current_monster)
					if d > 0:
						self.push(f"You hit {self.current_monster.name} for {d} damage.")
					else:
						self.push("You miss!")
					if not self.current_monster.is_alive():
						self.push(f"{self.current_monster.name} has been defeated!")
						# handle loot
						p = self.game.handle_loot(self.current_monster)
						if p:
							self.hero.add_potion(p)
							self.push(f"You found a {p.name}!")
						# award gold reward for defeating the monster
						gold = self.game.gold_reward(self.current_monster)
						if gold > 0:
							self.hero.add_gold(gold)
							self.push(f"You gained {gold} gold.")
							# instruct player how to access the menu/castle after combat
							self.push("Open the main menu with 'm' to return to the Castle.")
						self.mode = 'explore'
						self.current_monster = None
						continue
					# monster turn
					md = self.game.attack(self.current_monster, self.hero)
					if md > 0:
						self.push(f"{self.current_monster.name} hits you for {md} damage.")
					else:
						self.push(f"{self.current_monster.name} misses!")
					if not self.hero.is_alive():
						self.push("You have been slain! Game over.")
						self.push("Press 'r' to restart or 'q' to quit.")
						self.mode = 'dead'
						self.current_monster = None
						continue
				elif c == ord('r'):
					if self.game.attempt_flee(self.hero, self.current_monster):
						self.push("You fled successfully.")
						self.mode = 'explore'
						self.current_monster = None
					else:
						self.push("Flee failed!")
						# monster gets a free attack
						md = self.game.attack(self.current_monster, self.hero)
						if md > 0:
							self.push(f"{self.current_monster.name} hits you for {md} damage.")
						else:
							self.push(f"{self.current_monster.name} misses!")
						if not self.hero.is_alive():
							self.push("You have been slain! Game over.")
							self.push("Press 'r' to restart or 'q' to quit.")
							self.mode = 'dead'
							self.current_monster = None
							continue


def run_curses(hero: Entity):
	game = Game()
	def _wrapped(stdscr):
		ui = CursesUI(stdscr, hero, game)
		ui.mainloop()

	curses.wrapper(_wrapped)