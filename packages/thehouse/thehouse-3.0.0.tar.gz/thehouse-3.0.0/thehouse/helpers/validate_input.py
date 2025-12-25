"""validate_input.

This function will validate input.
"""
from .print_pause import print_pause


def validate_input(prompt, options):
    """Validate the input from the user.

    :param options: a list of eligible options.
    """
    while True:
        try:
            option = input(prompt).lower()
        except KeyboardInterrupt:
            print_pause("Goodbye!")
            quit()

        if option in options:
            return option
        elif option == "quit":
            print_pause("Goodbye!")
            quit()

        print("Sorry, I didn't understand! Try Again!")
