from dataclasses import dataclass, field
from random import randint
from typing import List, Optional, Dict, Any
import json


@dataclass
class Potion:
	name: str
	heal: int

	def to_dict(self) -> Dict[str, Any]:
		return {"name": self.name, "heal": self.heal}

	@staticmethod
	def from_dict(d: Dict[str, Any]) -> 'Potion':
		return Potion(name=d["name"], heal=int(d["heal"]))


@dataclass
class Weapon:
	name: str
	damage: int
	cost: int

	def to_dict(self) -> Dict[str, Any]:
		return {"name": self.name, "damage": self.damage, "cost": self.cost}

	@staticmethod
	def from_dict(d: Dict[str, Any]) -> 'Weapon':
		return Weapon(name=d["name"], damage=int(d["damage"]), cost=int(d["cost"]))


@dataclass
class Armor:
	name: str
	value: int
	cost: int

	def to_dict(self) -> Dict[str, Any]:
		return {"name": self.name, "armor": self.value, "cost": self.cost}

	@staticmethod
	def from_dict(d: Dict[str, Any]) -> 'Armor':
		return Armor(name=d["name"], value=int(d["armor"]), cost=int(d["cost"]))


@dataclass
class Entity:
	"""Classe de base pour Player et Monster contenant les champs et comportements communs."""
	name: str
	hp: int
	max_hp: int

	def attack_roll(self) -> int:
		return randint(1, 20)

	def attack(self, other) -> int:
		""" Effectue une attaque sur une autre entité.
			Renvoie les dégâts infligés (0 si manqué).
		"""
		if self.attack_roll() >= other.armor_class:
			damage = self.damage
			other.hp = max(0, other.hp - damage)
			return damage
		return 0

	def is_alive(self) -> bool:
		return self.hp > 0

	@property
	def armor_class(self):
		"""À redéfinir dans les sous-classes."""
		raise NotImplementedError("armor_class doit être défini dans les sous-classes")

	@property
	def damage(self):
		"""À redéfinir dans les sous-classes."""
		raise NotImplementedError("damage doit être défini dans les sous-classes")


@dataclass
class Monster(Entity):
	_damage: int = field(default=2)
	armor: int = field(default=10)

	@property
	def armor_class(self):
		return self.armor

	@property
	def damage(self):
		return self._damage


@dataclass
class Player(Entity):
	gold: int = 0
	inventory: List[Potion] = field(default_factory=list)
	weapons: List[Weapon] = field(default_factory=list)
	armors: List[Armor] = field(default_factory=list)
	equipped_weapon: Optional[Weapon] = None
	equipped_armor: Optional[Armor] = None

	@property
	def armor_class(self):
		return self.equipped_armor.value if self.equipped_armor else 10

	@property
	def damage(self):
		return 2 + self.equipped_weapon.damage if self.equipped_weapon else 2

	def unequip_weapon(self) -> bool:
		if self.equipped_weapon:
			self.equipped_weapon = None
			return True
		return False

	def unequip_armor(self) -> bool:
		if self.equipped_armor:
			self.equipped_armor = None
			return True
		return False

	def heal(self, amount: int) -> None:
		self.hp = min(self.max_hp, self.hp + amount)

	# Inventory methods for potions
	def add_potion(self, potion: Potion) -> None:
		self.inventory.append(potion)

	def list_potions(self) -> List[Potion]:
		return [p for p in self.inventory]

	def drink_potion(self, index: int) -> Optional[int]:
		"""Drink potion by index in inventory. Returns amount healed or None if invalid index."""
		if index < 0 or index >= len(self.inventory):
			return None
		p = self.inventory.pop(index)
		before = self.hp
		self.heal(p.heal)
		healed = self.hp - before
		return healed

	# Gold and shop related
	def add_gold(self, amount: int) -> None:
		self.gold += amount

	def spend_gold(self, amount: int) -> bool:
		if amount <= self.gold:
			self.gold -= amount
			return True
		return False

	def add_weapon(self, weapon: Weapon) -> None:
		self.weapons.append(weapon)

	def add_armor(self, armor: Armor) -> None:
		self.armors.append(armor)

	def equip_weapon(self, index: int) -> bool:
		if index < 0 or index >= len(self.weapons):
			return False
		self.equipped_weapon = self.weapons[index]
		return True

	def equip_armor(self, index: int) -> bool:
		if index < 0 or index >= len(self.armors):
			return False
		# do not overwrite base armor; keep equipped_armor as a bonus
		self.equipped_armor = self.armors[index]
		return True

	def sell_weapon(self, index: int) -> Optional[int]:
		if index < 0 or index >= len(self.weapons):
			return None
		w = self.weapons.pop(index)
		# sell at half price
		value = w.cost // 2
		self.add_gold(value)
		# unequip if it was equipped (compare by identity)
		if self.equipped_weapon is w:
			self.equipped_weapon = None
		return value

	def sell_armor(self, index: int) -> Optional[int]:
		if index < 0 or index >= len(self.armors):
			return None
		a = self.armors.pop(index)
		value = a.cost // 2
		self.add_gold(value)
		# unequip if it was equipped (compare by identity)
		if self.equipped_armor is a:
			self.equipped_armor = None
		return value

	def to_dict(self) -> Dict[str, Any]:
		return {"name": self.name, "hp": self.hp, "max_hp": self.max_hp, "gold": self.gold, "inventory": [p.to_dict() for p in self.inventory], "weapons": [w.to_dict() for w in self.weapons], "armors": [a.to_dict() for a in self.armors], "equipped_weapon": self.equipped_weapon.to_dict() if self.equipped_weapon else None, "equipped_armor": self.equipped_armor.to_dict() if self.equipped_armor else None, }

	@staticmethod
	def from_dict(d: Dict[str, Any]) -> 'Player':
		inv = [Potion.from_dict(x) for x in d.get("inventory", [])]
		weps = [Weapon.from_dict(x) for x in d.get("weapons", [])]
		arms = [Armor.from_dict(x) for x in d.get("armors", [])]
		eq_w = Weapon.from_dict(d["equipped_weapon"]) if d.get("equipped_weapon") else None
		eq_a = Armor.from_dict(d["equipped_armor"]) if d.get("equipped_armor") else None
		player = Player(name=d.get("name", "Hero"), hp=int(d.get("hp", 10)), max_hp=int(d.get("max_hp", d.get("hp", 10))), inventory=inv, gold=int(d.get("gold", 0)), weapons=weps, armors=arms, equipped_weapon=eq_w, equipped_armor=eq_a, )
		return player

	def save_to_file(self, path: str) -> None:
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

	@staticmethod
	def load_from_file(path: str) -> Optional['Player']:
		try:
			with open(path, 'r', encoding='utf-8') as f:
				data = json.load(f)
			return Player.from_dict(data)
		except Exception:
			return None
