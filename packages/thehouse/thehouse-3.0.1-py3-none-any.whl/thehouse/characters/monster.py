"""Monster."""
import random

from .character import Character


class Monster(Character):
    """Monster class."""

    def __init__(self, player):
        """Inizialize the class with a player.

        :param player: the instantiated Player class.
        """
        super().__init__()
        self.player = player

    def __str__(self) -> str:
        """Return a string containing the health of the monster."""
        return f"Monster - health: {self.health}"

    def deal_damage(self) -> None:
        """Deal a random damage."""
        damage = random.randint(1, 2)
        self.player.lose_health(damage)
