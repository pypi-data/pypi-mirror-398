"""Room blueprint."""
from thehouse.helpers import print_pause, validate_input


class Room:
    """Room blueprint."""

    def __init__(self, player, thehouse):
        """Initialize the class.

        :param player: the instantiated Player class.
        :param thehouse: the instantiated TheHouse class.
        """
        self.player = player
        self.thehouse = thehouse

    def __str__(self):
        """Return the name of the room."""
        return self.__class__.__name__.lower()

    def blueprint(self) -> None:
        """Print all sides of the room.

        This method will be called if user type "help".
        """
        pass

    def right(self) -> str:
        """Print content of the right side of the room."""
        return str(self)

    def left(self) -> str:
        """Print content of the left side of theroom."""
        return str(self)

    def backward(self) -> str:
        """Print content of the back side of the room."""
        return str(self)

    def forward(self) -> str:
        """Print content of the front side of the room."""
        return str(self)

    def move(self) -> str:
        """Let the user move inside or outside the room."""
        while True:
            print_pause("Where do you want to go?")

            choice = validate_input(
                'Type "forward", "right", "backward", "left", "help", "items": ',
                ["right", "left", "forward", "backward", "help", "items"],
            )

            if choice == "right":
                return self.right()
            elif choice == "left":
                return self.left()
            elif choice == "backward":
                return self.backward()
            elif choice == "forward":
                return self.forward()
            elif choice == "help":
                self.blueprint()
            elif choice == "items":
                self.player.print_items()
