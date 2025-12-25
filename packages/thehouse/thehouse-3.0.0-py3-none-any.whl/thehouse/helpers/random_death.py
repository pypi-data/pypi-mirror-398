"""random_death.

This function will print a random death from the DEATHS variable.
It uses the print_pause funtion
"""

import random

from .print_pause import print_pause

DEATHS = [
    "Something utterly bad stabs you in the back. You died!",
    "A strange figure grabs you and kills you instantly!",
    "Something from the dark makes you so mad you die!",
]


def random_death():
    """Print a random death from DEATHS variable."""
    print_pause(random.choice(DEATHS), 3)
    print_pause("\n\n=== GAME OVER ===\n\n")
