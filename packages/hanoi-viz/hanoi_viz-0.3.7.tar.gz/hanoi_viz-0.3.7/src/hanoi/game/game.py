"""Main game logic for Towers of Hanoi."""

from __future__ import annotations

from collections import defaultdict

import pygame
from rich.console import Console

from hanoi import hanoi
from hanoi.cli import Settings

from .colors import Color
from .constants import (
    BOARD_HEIGHT,
    BOARD_POS_LEFT,
    BOARD_POS_TOP,
    BOARD_WIDTH,
    CAPTION,
    DISK_HEIGHT,
    DISK_WIDTH,
    FPS,
    HEIGHT,
    LIFT_Y,
    PEG_HEIGHT,
    PEG_WIDTH,
    PRE_START_DELAY_MS,
    WIDTH,
)
from .exceptions import QuitGame, ReturnToStartScreen

console = Console()


class Game:
    """Main game class for Towers of Hanoi."""

    def __init__(self, settings: Settings):
        self.settings = settings
        # pygame.init() is called in run_pygame, so we don't need to call it here
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.board = pygame.Rect(BOARD_POS_LEFT, BOARD_POS_TOP, BOARD_WIDTH, BOARD_HEIGHT)
        self.pegs = self._init_pegs()
        self.disks = self._init_disks(self.settings.n_disks)

        left, width, top = self.board.left - 20, self.board.width + 40, self.board.bottom + 10
        self.progress_border = pygame.Rect(left, top, width, 15)
        self.progress_bar = pygame.Rect(left, top, 0, 15)

        self.peg_stacks = defaultdict(list)
        self.peg_stacks[1].extend(self.disks)

        self.total_moves = 2**self.settings.n_disks - 1
        self.print_spaces = len(str(self.total_moves))
        self.print_disk_spaces = len(str(self.settings.n_disks))
        self.clock = pygame.time.Clock()

        self.finished = False
        self.paused = False
        self.step_once = False
        self.show_help = False

        # Initialize font for text display
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.help_title_font = pygame.font.Font(None, 36)
        self.help_font = pygame.font.Font(None, 28)
        self.current_move_text = None

        self._update_caption()

    def _init_pegs(self) -> list[pygame.Rect]:
        """Initialize the three pegs."""
        return [
            pygame.Rect(peg_num * WIDTH // 4, PEG_HEIGHT, PEG_WIDTH, self.board.top - PEG_HEIGHT)
            for peg_num in range(1, 4)
        ]

    def _init_disks(self, n_disks: int) -> list[pygame.Rect]:
        """Initialize the disks."""
        disks = []
        for i in range(n_disks, 0, -1):
            width = DISK_WIDTH if i == n_disks else int(disks[-1].width * 0.9)
            disk = pygame.Rect(0, 0, width, DISK_HEIGHT)
            disk.centerx = self.pegs[0].centerx
            disk.bottom = self.board.top if i == n_disks else disks[-1].top
            disks.append(disk)
        return disks

    def handle_events(self) -> None:
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise QuitGame
            if event.type == pygame.KEYDOWN:
                # If help is showing, only allow closing it or quitting
                if self.show_help:
                    if event.key == pygame.K_ESCAPE:
                        # ESC closes help
                        self.show_help = False
                    elif event.key == pygame.K_q:
                        # Q quits (even from help screen)
                        raise QuitGame
                    elif event.unicode == '?':
                        # "?" also closes help
                        self.show_help = False
                    continue

                # Handle help screen toggle
                if event.unicode == '?':
                    self.show_help = not self.show_help
                    if self.show_help and not self.paused and not self.finished:
                        # Pause the game when showing help (if game is running)
                        self.paused = True
                        self._update_caption()
                    continue

                # Normal game controls (only when help is not showing)
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    raise QuitGame
                if event.key == pygame.K_r:
                    raise ReturnToStartScreen
                if event.key in (pygame.K_SPACE, pygame.K_p):
                    self.paused = not self.paused
                    if not self.paused:
                        # Resuming from pause - exit step mode to allow continuous running
                        self.step_once = False
                    self._update_caption()
                elif event.key in (pygame.K_RIGHT, pygame.K_n):
                    self.step_once = True
                    if self.paused:
                        self.paused = False
                    self._update_caption()
                elif event.key == pygame.K_f:
                    self.settings.speed += 10
                    console.print(f'speed increased to: {self.settings.speed}')
                elif event.key == pygame.K_s:
                    self.settings.speed -= 10
                    if self.settings.speed < 10:
                        self.settings.speed = 10
                    console.print(f'speed decreased to: {self.settings.speed}')

    def _update_caption(self) -> None:
        """Update the window caption based on game state."""
        caption = CAPTION
        if not self.finished:
            if self.step_once:
                caption += '(Step)'
            elif self.paused:
                caption += ' (Paused)'
        pygame.display.set_caption(caption)

    def wait_if_paused(self) -> None:
        """Wait while the game is paused."""
        while self.paused:
            self.handle_events()
            self.refresh()

    def run(self) -> None:
        """Run the main game loop."""
        while True:
            self.refresh()

            # Pre-start delay: allow user to exit/pause/step before simulation begins
            start_time = pygame.time.get_ticks()
            while pygame.time.get_ticks() - start_time < PRE_START_DELAY_MS:
                self.handle_events()
                if self.step_once:  # If user pressed step, start immediately
                    break
                if self.paused:  # If paused, wait (user can still exit)
                    self.refresh()
                    continue
                self.refresh()  # Otherwise, continue waiting and refreshing

            move_iterator = enumerate(hanoi(self.settings.n_disks), 1)
            i = 0

            while True:
                self.handle_events()

                # If paused, wait (unless step_once is triggered, which will unpause)
                if self.paused and not self.step_once:
                    self.refresh()
                    continue

                # Execute next move
                try:
                    i, (disk, from_, to) = next(move_iterator)
                    move_text = (
                        f'{i:{self.print_spaces}}: Move disk {disk:{self.print_disk_spaces}} from peg {from_} to {to}.'
                    )
                    console.print(move_text)
                    self.current_move_text = move_text
                    self.move_disk(i, from_, to)

                    # If in step mode, pause after completing the move
                    if self.step_once:
                        self._update_caption()
                        self.paused = True
                        self.step_once = False
                except StopIteration:
                    self.finished = True
                    suffix = 's' if self.settings.n_disks > 1 else ''
                    completion_text = f'{self.settings.n_disks} disk{suffix} solved in {i} move{suffix}.'
                    console.print(f'\n[green]{completion_text}')
                    self.current_move_text = completion_text
                    self._update_caption()
                    while True:  # Wait for restart or quit
                        self.handle_events()
                        self.refresh()

    def refresh(self) -> None:
        """Refresh the game display."""
        self.screen.fill(Color.WHITE)
        pygame.draw.rect(self.screen, Color.BLACK, self.board)

        pygame.draw.rect(self.screen, Color.BLACK, self.progress_border, 2)
        pygame.draw.rect(self.screen, Color.GREEN, self.progress_bar)

        for peg in self.pegs:
            pygame.draw.rect(self.screen, Color.BLACK, peg)
        for i, disk in enumerate(self.disks):
            pygame.draw.rect(self.screen, Color.DISK_COLORS[i % len(Color.DISK_COLORS)], disk)

        help_surface = self.font.render('?', True, Color.GREY)
        help_rect = help_surface.get_rect(centerx=WIDTH - 20, centery=20)
        self.screen.blit(help_surface, help_rect)

        # Display current move text
        if self.current_move_text:
            text_surface = self.font.render(self.current_move_text, True, Color.BLACK)
            text_rect = text_surface.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 5)
            self.screen.blit(text_surface, text_rect)

        # Display help overlay if needed
        if self.show_help:
            self._render_help()

        pygame.display.flip()
        self.clock.tick(FPS)

    def _step_towards(
        self,
        rect: pygame.Rect,
        *,
        x: int | None = None,
        y: int | None = None,
        bottom: int | None = None,
    ) -> bool:
        """Move a rect one step towards the target position. Returns True if reached."""
        speed = self.settings.speed

        def approach(current: int, target: int) -> tuple[int, bool]:
            if current == target or abs(target - current) <= speed:
                return target, True
            return (current + speed if target > current else current - speed), False

        done = True
        if x is not None:
            rect.centerx, ok = approach(rect.centerx, x)
            done &= ok
        if y is not None:
            rect.centery, ok = approach(rect.centery, y)
            done &= ok
        if bottom is not None:
            rect.bottom, ok = approach(rect.bottom, bottom)
            done &= ok
        return done

    def _animate_to(
        self,
        rect: pygame.Rect,
        *,
        x: int | None = None,
        y: int | None = None,
        bottom: int | None = None,
    ) -> None:
        """Animate a rect to a target position."""
        done = False
        while not done:
            self.handle_events()
            self.wait_if_paused()
            done = self._step_towards(rect, x=x, y=y, bottom=bottom)
            self.refresh()

    def _render_help(self) -> None:
        # Create a semi-transparent overlay surface
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)  # Semi-transparent (0-255, higher = more opaque)
        overlay.fill(Color.BLACK)
        self.screen.blit(overlay, (0, 0))

        # Define keybindings to display
        keybindings = [
            ('?', 'Show/hide help'),
            ('esc / q', 'Quit game'),
            ('r', 'Return to start screen'),
            ('space / p', 'Pause/unpause'),
            ('right / n', 'Step once'),
            ('f', 'Increase speed'),
            ('s', 'Decrease speed'),
        ]

        # Calculate help box dimensions
        padding = 40
        line_height = 30
        box_width = 400
        box_height = len(keybindings) * line_height + padding * 2 + 60  # Extra space for title
        box_x = (WIDTH - box_width) // 2
        box_y = (HEIGHT - box_height) // 2

        # Draw help box background
        help_box = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(self.screen, Color.WHITE, help_box)
        pygame.draw.rect(self.screen, Color.BLACK, help_box, 3)

        # Render title
        title_text = self.help_title_font.render('Keyboard Controls', True, Color.BLACK)
        title_rect = title_text.get_rect(center=(WIDTH // 2, box_y + 30))
        self.screen.blit(title_text, title_rect)

        # Render keybindings
        y_offset = box_y + 70
        for key, description in keybindings:
            # Render key
            key_text = self.help_font.render(key, True, Color.BLUE)
            key_rect = key_text.get_rect(left=box_x + padding, centery=y_offset)
            self.screen.blit(key_text, key_rect)

            # Render description
            desc_text = self.help_font.render(description, True, Color.BLACK)
            desc_rect = desc_text.get_rect(left=box_x + padding + 145, centery=y_offset)
            self.screen.blit(desc_text, desc_rect)

            y_offset += line_height

        # Render close instruction
        close_text = self.font.render('Press ? or ESC to close', True, Color.GREY)
        close_rect = close_text.get_rect(center=(WIDTH // 2, box_y + box_height - 25))
        self.screen.blit(close_text, close_rect)

    def move_disk(self, step: int, from_peg: int, to_peg: int) -> None:
        """Move a disk from one peg to another."""
        disk = self.peg_stacks[from_peg].pop()

        final_width = self._calculate_progress(step)
        step_size = (final_width - self.progress_bar.width) // 3

        # raise disk
        self._animate_to(disk, y=LIFT_Y)
        self.progress_bar.width += step_size

        # move disk to next peg
        to_x = self.pegs[to_peg - 1].centerx
        self._animate_to(disk, x=to_x)
        self.progress_bar.width += step_size

        to_y = self.peg_stacks[to_peg][-1].top if self.peg_stacks[to_peg] else self.board.top
        self._animate_to(disk, bottom=to_y)
        self.progress_bar.width = final_width
        self.peg_stacks[to_peg].append(disk)

    def _calculate_progress(self, step: int) -> int:
        percent_complete = step / self.total_moves
        progress_width = round(percent_complete * self.progress_border.width)
        return progress_width
