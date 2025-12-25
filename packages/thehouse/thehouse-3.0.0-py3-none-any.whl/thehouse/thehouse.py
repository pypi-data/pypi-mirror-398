"""thehouse.

This class wraps all rooms and play the game
"""
import random

import thehouse.rooms as rooms
from thehouse.helpers import print_pause, random_death


class TheHouse:
    """TheHouse."""

    def __init__(self, player):
        """Inizialize class.

        :param player: the instantiated player class.
        """
        self.player = player

        # Rooms
        self.rooms = {
            "bedroom": rooms.Bedroom(self.player, self),
            "diningroom": rooms.Diningroom(self.player, self),
            "hall": rooms.Hall(self.player, self),
            "hallway": rooms.Hallway(self.player, self),
            "kitchen": rooms.Kitchen(self.player, self),
            "livingroom": rooms.Livingroom(self.player, self),
            "studio": rooms.Studio(self.player, self),
        }

        self.current_room = "bedroom"

    def introduction(self):
        print_pause("\n\n=== THE HOUSE ===\n\n", 3)

        print_pause("Someone, or something hit you and you faint.")
        print_pause(
            "You hear that this someone or something drags you to someplace.\n", 3
        )
        print_pause("You open your eyes and find yourself lying on the floor.")
        print_pause("Your head is pounding and it hurts.")
        print_pause("With a lot of effort you stand up.")

    def play(self):
        """Play engine."""
        self.introduction()

        while not self.player.escaped and self.player.is_alive:
            # a room's center() method returns the next room
            next_room = self.rooms[self.current_room].center()
            self.current_room = next_room

            # Check if player is still alive
            if not self.player.is_alive:
                random_death()
                print_pause("\n=== GAME OVER ===\n", 3)
                break

            # Check if player has escaped
            if self.player.escaped:
                print("\nCongratulations! You beat the game!\n")
                break
