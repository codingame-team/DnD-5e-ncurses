from dataclasses import dataclass
from random import randint


@dataclass
class Entity:
	name: str
	hp: int
	damage: int
	max_hp: int
	armor: int

	def attack(self, other):
		print(f'{self.name} attacks {other.name}...')
		attack_roll = randint(1, 20)
		if attack_roll >= other.armor:
			other.hp -= self.damage
			print(f'{other.name} is hit for {self.damage} hit points!')
		else:
			print(f'{self.name} misses!')


if __name__ == '__main__':
	player = Entity(name='Hero', hp=30, damage=5, max_hp=30, armor=15)
	monster = Entity(name='Goblin', hp=20, damage=3, max_hp=20, armor=12)

	round = 0
	while player.hp > 0 and monster.hp > 0:
		round += 1
		print(f'****** Round #{round} *******')
		player.attack(monster)
		if monster.hp <= 0:
			print(f'{monster.name} has been defeated!')
			break
		monster.attack(player)
		if player.hp <= 0:
			print(f'{player.name} has been defeated!')
			break
		print(f'{player.name} HP: {player.hp}, {monster.name} HP: {monster.hp}\n')
