"""HALL.

Sides:
- FORWARD: the main door of the house.
- RIGHT: door to the diningroom.
- BACKWARD: hallway.
- LEFT: kitchen.
"""

from thehouse.helpers import print_pause
from thehouse.helpers.constants import HOUSE_KEY_1, HOUSE_KEY_2, HOUSE_KEY_3

from .room import Room


class Hall(Room):
    """Hall."""

    def blueprint(self) -> None:
        """Print blueprint of the house."""
        print_pause("- In front of you there's the main door of the house.")
        print_pause("- On your right there's a door.")
        print_pause("- Backwards there's the hallway.")
        print_pause("- On your left there's another door.")

    def center(self):
        """Print welcome message."""
        print_pause("You're in the hall!")
        self.blueprint()
        return self.move()

    def backward(self):
        """Move the player to the hallway."""
        return "hallway"

    def left(self):
        """Move the player to the kitchen."""
        print_pause("You open the door and enter the room.")
        return "kitchen"

    def right(self):
        """Move the player to the diningroom."""
        print_pause("You open the door and enter the room.")
        return "diningroom"

    def forward(self):
        """Move the player towards the main door of the house."""
        if (
            HOUSE_KEY_1 in self.player.items
            and HOUSE_KEY_2 in self.player.items
            and HOUSE_KEY_3 in self.player.items
        ):
            print_pause("You unlock the door and finally exit the house!")
            self.player.escaped = True
        else:
            print_pause("You need three keys to open the door!")
            print_pause("You go back.")

        return str(self)
