"""Bedroom.

Sides:
- FORWARD: dresser
- RIGHT: window
- BACKWARD: bed
- LEFT: door to the hallway
"""

import random

from thehouse.helpers import print_pause, validate_input
from thehouse.helpers.constants import HOUSE_KEY_1

from .room import Room


class Bedroom(Room):
    """Bedroom."""

    def __init__(self, player, thehouse):
        """Initialize the class.

        :param player: the instantiated Player class.
        :param thehouse: the instantiated TheHouse class.
        """
        super().__init__(player, thehouse)
        self.key_in_drawer = random.randint(1, 5)

    def blueprint(self) -> None:
        """Print the blueprint of the room."""
        print_pause("- In front of you, there's a dresser.")
        print_pause("- On your right, there's a window.")
        print_pause("- Behind you, there's a bed.")
        print_pause("- On your left, there's a door.")

    def center(self):
        """Print welcome message."""
        print_pause("You're in the bedroom!")
        self.blueprint()
        return self.move()

    def left(self):
        """Move player to the left side of the room."""
        print_pause("You open the door and enter the room.")
        return "hallway"

    def backward(self):
        """Move player to the back side of the room."""
        print_pause("You look tired.")
        print_pause("Do you want to rest a little?")

        choice = validate_input("Type yes or no: ", ["yes", "no"])

        if choice == "yes":
            print_pause("You decide to rest.", 2)
            print_pause(".", 2)
            print_pause(".", 2)
            print_pause(".", 2)
            self.player.restore_health()
        else:
            print_pause("You go back.")

        return str(self)

    def right(self):
        """Print content of the right side of the room."""
        print_pause("You look out the window.")
        print_pause("Outside, it's pitch black!")
        print_pause("Something is moving in the darkness.")
        print_pause("It's moving so fast that you can barely see it...")
        print_pause("You wonder how you could escape this house.")
        print_pause("And if it's even safe outside...", 3)
        print_pause("You go back.")

        return str(self)

    def forward(self):
        """Print content of the front side of the room."""
        print_pause("There are five drawers.")
        print_pause("1. Open the first.")
        print_pause("2. Open the second.")
        print_pause("3. Open the third.")
        print_pause("4. Open the fourth.")
        print_pause("5. Open the fifth.")

        return self.pick_a_drawer()

    def pick_a_drawer(self):
        """Let the user pick a drawer."""
        while self.player.is_alive:
            choice = validate_input(
                "Type a number between 1 and 5 included, or back: ",
                ["1", "2", "3", "4", "5", "back"],
            )

            if choice == "back":
                print_pause("You go back to the center of the room.")
                return str(self)
            else:
                print_pause(
                    "There are some clothes in it. You dig through them to find something..."
                )

                if int(choice) == self.key_in_drawer:
                    if HOUSE_KEY_1 in self.player.items:
                        print_pause("You've already picked a key from this drawer!")
                        print_pause("There's nothing more in it.")
                    else:
                        print_pause("You've found a key!")
                        self.player.pick_an_item(HOUSE_KEY_1)
                else:
                    print_pause("There's nothing between the clothes.")
                    print_pause("Something outside is moving...")
                    self.player.lose_health()
        return str(self)
