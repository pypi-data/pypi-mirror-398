"""This file is responsible of exporting all rooms."""
from .bedroom import Bedroom
from .diningroom import Diningroom
from .hall import Hall
from .hallway import Hallway
from .kitchen import Kitchen
from .livingroom import Livingroom
from .studio import Studio

__all__ = [
    "Bedroom",
    "Diningroom",
    "Hall",
    "Hallway",
    "Kitchen",
    "Livingroom",
    "Studio",
]
