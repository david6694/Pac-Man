"""Common constants for the display layer."""

from engine import GhostName

# Colors
BLACK = (0, 0, 0)
BLUE = (33, 33, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
PINK = (255, 182, 193)
CYAN = (0, 255, 255)
ORANGE = (255, 182, 85)
DARK_BLUE = (0, 0, 100)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (200, 200, 200)

GHOST_COLORS = {
    GhostName.BLINKY: RED,
    GhostName.PINKY: PINK,
    GhostName.INKY: CYAN,
    GhostName.CLYDE: ORANGE,
}
