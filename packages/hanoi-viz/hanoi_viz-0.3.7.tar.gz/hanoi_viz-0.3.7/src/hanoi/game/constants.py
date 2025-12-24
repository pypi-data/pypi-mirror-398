"""Game constants for rendering and animation."""

from typing import Final

# Frame rate
FPS: Final[int] = 60

# Screen dimensions
WIDTH: Final[int] = 800
HEIGHT: Final[int] = 400

# Board dimensions
BOARD_POS_LEFT: Final[int] = int(0.1 * WIDTH)
BOARD_POS_TOP: Final[int] = int(0.9 * HEIGHT)
BOARD_WIDTH: Final[int] = WIDTH - 2 * BOARD_POS_LEFT
BOARD_HEIGHT: Final[int] = int(0.02 * HEIGHT)

# Peg dimensions
PEG_HEIGHT: Final[int] = HEIGHT // 2
PEG_WIDTH: Final[int] = 6

# Disk dimensions
DISK_HEIGHT: Final[int] = 10
DISK_WIDTH: Final[int] = 120

# Animation
LIFT_Y: Final[int] = HEIGHT // 3

# Pre-start delay (in milliseconds) before simulation begins
PRE_START_DELAY_MS: Final[int] = 2000

CAPTION: Final[str] = 'Towers of Hanoi'
