"""Game-specific exceptions."""


class QuitGame(Exception):
    """Raised to stop the game loop cleanly when the window is closed."""


class ReturnToStartScreen(Exception):
    """Raised to return to the start screen from the game."""
