from random import randint, random
from typing import Optional, Tuple, List
from entities import Entity, Potion, Weapon, Armor, Monster, Player


class Game:
	"""Encapsulates non-UI game logic: wandering, encounters, combat resolution."""

	def __init__(self, seed: Optional[int] = None):
		self.rng_seed = seed
		# If deterministic behavior required, user can set seed externally via random.seed(seed)

	def create_healing_potion(self, small: bool = True) -> Potion:
		if small:
			return Potion(name='Small Healing Potion', heal=5)
		return Potion(name='Large Healing Potion', heal=12)

	def generate_monster(self, difficulty: int = 1) -> Entity:
		# Simple monster generator: scale hp and damage with difficulty
		hp = 8 + randint(0, 4) * difficulty
		damage = 2 + randint(0, 2) * difficulty
		armor = 10 + randint(0, 2)
		return Monster(name='Goblin', hp=hp, _damage=damage, max_hp=hp, armor=armor)

	def wander(self, hero: Player) -> Tuple[str, Optional[Entity]]:
		"""Hero wanders: either finds nothing or encounters a monster.
		Return: (message, monster_or_None)
		"""
		roll = randint(1, 100)
		if roll <= 40:
			# 40% chance nothing
			return ("You wander the dungeon but find nothing.", None)
		elif roll <= 85:
			# 45% chance small encounter
			monster = self.generate_monster(difficulty=1)
			return (f"A {monster.name} appears!", monster)
		else:
			# 15% chance tougher monster
			monster = self.generate_monster(difficulty=2)
			monster.name = 'Orc'
			return (f"A {monster.name} appears!", monster)

	def attack(self, attacker: Entity, defender: Entity) -> int:
		"""Resolve an attack; returns damage dealt."""
		dmg = attacker.attack(defender)
		return dmg

	def attempt_flee(self, hero: Player, monster: Monster) -> bool:
		"""Hero attempts to flee: success chance based on random roll and simple modifier.
		Returns True if flee succeeded.
		"""
		chance = 0.6
		# small modifier: if hero has more hp than monster, easier to flee
		if hero.hp > monster.hp:
			chance += 0.1
		return random() < chance

	def clamp_hp(self, entity: Entity) -> None:
		entity.hp = max(0, min(entity.max_hp, entity.hp))

	def handle_loot(self, monster: Monster) -> Optional[Potion]:
		"""When a monster is defeated, there is a chance to drop a healing potion."""
		# 30% chance to drop a small potion, 5% chance large
		roll = randint(1, 100)
		if roll <= 5:
			return self.create_healing_potion(small=False)
		if roll <= 35:
			return self.create_healing_potion(small=True)
		return None

	def gold_reward(self, monster: Monster) -> int:
		"""Compute gold reward from defeating a monster."""
		# base on monster max_hp and damage
		base = max(1, monster.max_hp // 2 + monster.damage)
		# randomize a bit
		return randint(base, base + 5)

	def get_shop_weapons(self) -> List[Weapon]:
		# static list for the shop
		return [
			Weapon(name='Short Sword', damage=2, cost=10),
			Weapon(name='Long Sword', damage=4, cost=20),
			Weapon(name='Great Axe', damage=6, cost=35),
		]

	def get_shop_armors(self) -> List[Armor]:
		return [
			Armor(name='Leather Armor', value=12, cost=12),
			Armor(name='Chain Mail', value=16, cost=28),
			Armor(name='Plate Armor', value=20, cost=50),
		]