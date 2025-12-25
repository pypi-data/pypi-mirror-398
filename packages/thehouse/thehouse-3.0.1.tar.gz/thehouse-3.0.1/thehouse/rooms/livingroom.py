"""Living Room.

Sides:
- FORWARD: safe
- RIGHT: door to the hallway
- BACKWARD: window
- LEFT: window
"""

import random

from thehouse.characters import Monster
from thehouse.helpers import print_pause, validate_input
from thehouse.helpers.constants import HOUSE_KEY_3, KNIFE, PASSEPARTOUT

from .room import Room


class Livingroom(Room):
    """Livingroom."""

    def __init__(self, player, thehouse):
        """Initialize class.

        :param player: the instantiated Player class.
        :param thehouse: the instantiated TheHouse class.
        """
        super().__init__(player, thehouse)
        self.monster = Monster(self.player)
        self.tries = random.randint(3, 6)
        self.safe_open = False
        self.safe_combination = random.randint(1, 9999)

    def blueprint(self) -> None:
        """Print blueprint of the room."""
        print_pause("- In front of you there's a painting.")
        print_pause("- On your right there's a door.")
        print_pause("- On your back there's a window.")
        print_pause("- On your left there's another window.")

    def center(self):
        """Print welcome message."""
        if self.monster.is_alive:
            print_pause("There's a terrible monster!")
            print_pause("It's half human and half something indescribable!")
            print_pause(
                "Luckily, it's slow, but one of its tentacles tries to grab you!"
            )
            return self.fight_or_escape()
        else:
            print_pause("You're in the livingroom!")
            self.blueprint()
            return self.move()

    def fight_or_escape(self):
        """Let user chose where to fight or escape."""
        print_pause("Do you want to fight or escape?")
        choice = validate_input("Type fight or escape: ", ["fight", "escape"])

        if choice == "fight":
            return self.fight()
        else:
            return self.escape()

    def fight(self):
        """Let the user fight the monster."""
        if self.monster.is_alive and self.player.is_alive:
            print_pause("It's your turn to deal damages!")

            if KNIFE not in self.player.items:
                damage = 1
                print_pause("It seems like you need something to deal more damages!")
            else:
                damage = random.randint(2, 4)

            print_pause(f"You deal {damage} damage.")
            self.monster.lose_health(damage)

            if self.monster.is_alive:
                print_pause("It's the monster's turn to deal damages!")
                self.monster.deal_damage()

                if self.player.is_alive:
                    return self.fight_or_escape()
                else:
                    return str(self)
            else:
                print_pause("You successfully killed the monster!")
                print_pause("The monster has dropped a key.")
                self.player.pick_an_item(PASSEPARTOUT)
                self.thehouse.rooms["studio"].door_locked = False
                return self.center()
        return str(self)

    def escape(self):
        """Let the user try to escape the monster."""
        print_pause("You're trying to escape the monster!")

        choice = validate_input(
            "Type a number between 1 and 6 included: ", ["1", "2", "3", "4", "5", "6"]
        )

        if int(choice) == random.randint(1, 6):
            print_pause("You successfully escaped the monster!")
            return "hallway"
        else:
            print_pause("You panic and can't escape the fight.")
            self.tries -= 1

            if self.tries <= 0:
                print_pause("The monster has reached you!")
                self.monster.deal_damage()
                self.tries = random.randint(3, 6)

                if self.player.is_alive:
                    return self.fight_or_escape()
                else:
                    return str(self)
            else:
                return self.fight_or_escape()

    def right(self):
        """Move the user towards the hallway."""
        print_pause("You open the door and enter the room.")
        return "hallway"

    def backward(self):
        """Move the user towards the window."""
        print_pause("There's a window and you look outside.")
        print_pause("There's a car! Maybe you can use it to escape from this house!")
        print_pause("You go back.")
        return str(self)

    def left(self):
        """Move the user towards left."""
        print_pause("There's a balcony.")
        print_pause("Outside, there's a garden.")
        print_pause("The low lights make the garden look bleak.")
        print_pause("You go back.")
        return str(self)

    def forward(self):
        """Move the user towards the safe."""
        if self.safe_open:
            print_pause("You opened the safe already and picked THE HOUSE KEY 3.")
            print_pause("You go back.")
            return str(self)
        else:
            print_pause("There's a painting...")
            print_pause("You look closely and see there's something behind it!")
            print_pause("You move the painting and reveal a safe!")
            print_pause("Maybe you can break it open!")

            return self.break_open()

    def break_open(self):
        """Let the user break open the safe."""
        print_pause("You need a combination!")

        while True:
            choice = validate_input(
                "Pick a combination between 0000 and 9999 included, or type back: ",
                [str(self.safe_combination), "back"],
            )

            if choice == "back":
                return str(self)
            else:
                if int(choice) == self.safe_combination:
                    print_pause("You successfully opened the safe!")
                    print_pause("Inside, there's a key!")
                    self.player.pick_an_item(HOUSE_KEY_3)
                    self.safe_open = True

                    return str(self)
                else:
                    print_pause("The combination is wrong! Try again!")
