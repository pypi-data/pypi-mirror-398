"""Color definitions for the game."""

from typing import List, Tuple


class Color:
    """Color constants for rendering."""

    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREY = (143, 143, 143)
    RED = (168, 50, 50)
    ORANGE = (207, 138, 21)
    BURNT_ORANGE = (255, 132, 0)
    YELLOW = (201, 193, 26)
    GREEN = (70, 189, 19)
    BLUE = (19, 150, 194)
    LIGHT_BLUE = (42, 191, 250)
    PURPLE = (153, 13, 191)
    LIGHT_PURPLE = (207, 99, 190)

    DISK_COLORS: List[Tuple[int, int, int]] = [
        RED,
        ORANGE,
        YELLOW,
        GREEN,
        BLUE,
        PURPLE,
        GREY,
        BURNT_ORANGE,
        LIGHT_BLUE,
        LIGHT_PURPLE,
    ]
