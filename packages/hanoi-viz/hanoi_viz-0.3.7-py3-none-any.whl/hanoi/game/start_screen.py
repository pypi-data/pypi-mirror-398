"""Start screen for configuring game parameters."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

import pygame

from hanoi.cli import Settings

from .colors import Color
from .constants import FPS, HEIGHT, WIDTH
from .exceptions import QuitGame


class FieldType(str, Enum):
    """Field identifiers for the start screen."""

    N_DISKS = 'n_disks'
    SPEED = 'speed'
    START_BUTTON = 'start_button'


@dataclass
class InputField:
    """Represents an input field in the start screen."""

    field_type: FieldType
    label: str
    value: int
    input_text: str = ''
    validator: Callable[[int], int] = field(default=lambda x: x)

    def __post_init__(self):
        if not self.input_text:
            self.input_text = str(self.value)

    def commit(self) -> None:
        """Commit the input text to the value."""
        try:
            parsed = int(self.input_text.strip())
            self.value = self.validator(parsed)
            self.input_text = str(self.value)
        except ValueError:
            self.input_text = str(self.value)


class StartScreen:
    """Start screen for configuring game parameters before starting."""

    def __init__(self, screen: pygame.Surface, default_settings: Settings):
        self.screen = screen
        self.default_settings = default_settings

        # Define input fields
        self.fields: dict[FieldType, InputField] = {
            FieldType.N_DISKS: InputField(
                field_type=FieldType.N_DISKS,
                label='Number of Disks (1-15):',
                value=default_settings.n_disks,
                validator=lambda x: max(1, min(x, 15)),
            ),
            FieldType.SPEED: InputField(
                field_type=FieldType.SPEED,
                label='Speed (pixels/frame):',
                value=default_settings.speed,
                validator=lambda x: max(1, x),
            ),
        }

        # Field order for navigation
        self.field_order = [FieldType.N_DISKS, FieldType.SPEED, FieldType.START_BUTTON]

        # Active field and editing state
        self.active_field: FieldType = FieldType.N_DISKS
        self.editing = False

        # Fonts
        pygame.font.init()
        self.title_font = pygame.font.Font(None, 48)
        self.label_font = pygame.font.Font(None, 32)
        self.input_font = pygame.font.Font(None, 28)
        self.button_font = pygame.font.Font(None, 36)

        # Colors
        self.bg_color = Color.WHITE
        self.text_color = Color.BLACK
        self.active_color = Color.LIGHT_BLUE
        self.inactive_color = Color.GREY
        self.button_color = Color.GREEN

    def handle_event(self, event: pygame.event.Event) -> Settings | None:
        """Handle events. Returns Settings if start is pressed, None otherwise."""
        if event.type != pygame.KEYDOWN:
            return None

        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            raise QuitGame

        if event.key == pygame.K_UP or (event.key == pygame.K_TAB and (event.mod & pygame.KMOD_SHIFT)):
            self._navigate_up()
            return None

        if event.key in (pygame.K_TAB, pygame.K_DOWN):
            self._navigate_down()
            return None

        # Start game or toggle edit mode
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.active_field == FieldType.START_BUTTON:
                return self._create_settings()
            self._toggle_edit_mode()
            return None

        # Handle text input
        if self.active_field in self.fields:
            if self.editing:
                self._handle_text_input(event)
            elif event.unicode.isdigit():
                self.editing = True  # Start editing when typing a number
                self.fields[self.active_field].input_text = event.unicode

        return None

    def _navigate_up(self) -> None:
        """Navigate to the previous field."""
        if self.editing and self.active_field in self.fields:
            self._commit_field()
        current_index = self.field_order.index(self.active_field)
        new_index = (current_index - 1) % len(self.field_order)
        self.active_field = self.field_order[new_index]
        self.editing = False

    def _navigate_down(self) -> None:
        """Navigate to the next field."""
        if self.editing and self.active_field in self.fields:
            self._commit_field()
        current_index = self.field_order.index(self.active_field)
        new_index = (current_index + 1) % len(self.field_order)
        self.active_field = self.field_order[new_index]
        self.editing = False

    def _toggle_edit_mode(self) -> None:
        """Toggle edit mode for the current field."""
        if self.editing:
            self._commit_field()
            self.editing = False
        else:
            self.editing = True

    def _handle_text_input(self, event: pygame.event.Event) -> None:
        """Handle text input when editing a field."""
        field = self.fields[self.active_field]
        if event.key == pygame.K_BACKSPACE:
            if field.input_text:
                field.input_text = field.input_text[:-1]
        elif event.unicode.isdigit():
            field.input_text += event.unicode

    def _commit_field(self) -> None:
        """Commit the current field value and validate it."""
        if self.active_field not in self.fields:
            return
        self.fields[self.active_field].commit()

    def _create_settings(self) -> Settings:
        """Create Settings object from current values."""
        # Commit any field that's being edited
        if self.editing and self.active_field in self.fields:
            self._commit_field()
        return Settings(
            n_disks=self.fields[FieldType.N_DISKS].value,
            speed=self.fields[FieldType.SPEED].value,
            animate=True,
        )

    def render(self) -> None:
        """Render the start screen."""
        self.screen.fill(self.bg_color)

        # Title
        self._render_title()

        # Configuration fields
        y_start = 140
        spacing = 60
        self._render_field(FieldType.N_DISKS, y_start)
        self._render_field(FieldType.SPEED, y_start + spacing)

        # Start button
        self._render_button(FieldType.START_BUTTON, 'Start Game', y_start + 2 * spacing + 20)

        # Instructions
        self._render_instructions()

        pygame.display.flip()

    def _render_title(self) -> None:
        """Render the title and subtitle."""
        title_text = self.title_font.render('Towers of Hanoi', True, self.text_color)
        title_rect = title_text.get_rect(center=(WIDTH // 2, 40))
        self.screen.blit(title_text, title_rect)

        subtitle_text = self.label_font.render('Configure Simulation Settings', True, self.inactive_color)
        subtitle_rect = subtitle_text.get_rect(center=(WIDTH // 2, 80))
        self.screen.blit(subtitle_text, subtitle_rect)

    def _render_instructions(self) -> None:
        """Render the instruction text."""
        inst_text = self._get_instruction_text()
        inst_surface = self.label_font.render(inst_text, True, self.inactive_color)
        inst_rect = inst_surface.get_rect(center=(WIDTH // 2, HEIGHT - 20))
        self.screen.blit(inst_surface, inst_rect)

    def _get_instruction_text(self) -> str:
        """Get the instruction text based on current state."""
        if self.active_field == FieldType.START_BUTTON:
            return 'Press Enter or Space to start the game'
        elif self.editing:
            return 'Type numbers, Enter to confirm, Tab/Arrow keys to navigate'
        else:
            return 'Press Enter to edit, Tab/Arrow keys to navigate, Enter on Start to begin'

    def _render_field(self, field_type: FieldType, y: int) -> None:
        """Render a labeled input field."""
        field = self.fields[field_type]
        is_active = self.active_field == field_type
        is_editing = is_active and self.editing

        # Label
        label_color = self.active_color if is_active else self.text_color
        label_surface = self.label_font.render(field.label, True, label_color)
        label_rect = label_surface.get_rect(midright=(WIDTH // 2 - 20, y))
        self.screen.blit(label_surface, label_rect)

        # Input box
        input_color = self.active_color if is_active else self.inactive_color
        input_rect = pygame.Rect(WIDTH // 2 + 20, y - 15, 100, 30)
        border_width = 3 if is_editing else 2
        pygame.draw.rect(self.screen, input_color, input_rect, border_width)

        # Input text with cursor
        display_text = field.input_text if field.input_text else '0'
        if is_editing:
            display_text += '|'
        text_surface = self.input_font.render(display_text, True, self.text_color)
        text_rect = text_surface.get_rect(midleft=(input_rect.left + 5, input_rect.centery))
        self.screen.blit(text_surface, text_rect)

    def _render_button(self, field_type: FieldType, text: str, y: int) -> None:
        """Render a button."""
        is_active = self.active_field == field_type
        button_color = self.active_color if is_active else self.button_color
        button_rect = pygame.Rect(WIDTH // 2 - 100, y - 20, 200, 40)

        pygame.draw.rect(self.screen, button_color, button_rect)
        pygame.draw.rect(self.screen, self.text_color, button_rect, 2)

        text_surface = self.button_font.render(text, True, self.text_color)
        text_rect = text_surface.get_rect(center=button_rect.center)
        self.screen.blit(text_surface, text_rect)

    def run(self) -> Settings:
        """Run the start screen loop. Returns Settings when user starts the game."""
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise QuitGame

                settings = self.handle_event(event)
                if settings is not None:
                    return settings

            self.render()
            clock.tick(FPS)
