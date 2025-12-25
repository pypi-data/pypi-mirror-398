"""This module is responsible of initializing the game."""
from thehouse.characters import Player
from thehouse.helpers import print_pause, validate_input
from thehouse.thehouse import TheHouse


def main():
    while True:
        player = Player()
        game = TheHouse(player)

        game.play()

        print_pause("Do you want to play again?")
        choice = validate_input("Type yes or no: ", ["yes", "no"])

        if choice == "no":
            break


if __name__ == "__main__":
    main()
