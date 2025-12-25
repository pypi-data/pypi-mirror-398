"""print_pause.

This function will print a message and then it will pause the terminal
"""

import time


def print_pause(string, sleep=1):
    """Print a message and pause the terminal.

    :param sleep: the amount of seconds the terminal should sleep as integer.
    """
    try:
        print(string)

        try:
            time.sleep(sleep)
        except TypeError:
            time.sleep(1)
    except KeyboardInterrupt:
        print_pause("Goodbye!")
        quit()
