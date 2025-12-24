"""Game package for Towers of Hanoi pygame implementation."""

from __future__ import annotations

import pygame
from rich.console import Console

from hanoi.cli import Settings

from .constants import CAPTION, HEIGHT, WIDTH
from .exceptions import QuitGame, ReturnToStartScreen
from .game import Game
from .start_screen import StartScreen

console = Console()


def run_pygame(settings: Settings) -> None:
    """Run the pygame-based Towers of Hanoi game.

    Args:
        settings: Game settings including number of disks and animation speed.
    """
    try:
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(CAPTION)
        current_settings = settings

        # Main loop: start screen -> game -> start screen (on restart)
        while True:
            # Show start screen
            start_screen = StartScreen(screen, current_settings)
            final_settings = start_screen.run()
            current_settings = final_settings

            # Create game with final settings (pygame already initialized)
            game = Game(final_settings)
            try:
                game.run()
            except ReturnToStartScreen:
                # Return to start screen with current settings
                console.print('[blue]returning to start...')
                continue
    except QuitGame:
        console.print('[blue]quitting game...')
    except KeyboardInterrupt:
        console.print('[yellow]received interrupt, quitting game...')


__all__ = ['run_pygame']
