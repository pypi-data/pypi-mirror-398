"""Modal dialog system for token-audit TUI.

Provides reusable modal components for:
- SelectModal: Radio button selection (platform picker)
- ConfirmModal: Yes/No confirmation (delete session)
- InputModal: Text input with validation (date range)

v1.0.3 - task-233.1
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple

from rich import box
from rich.align import Align
from rich.panel import Panel
from rich.text import Text

from .keyboard import KEY_BACKSPACE, KEY_DOWN, KEY_ENTER, KEY_ESC, KEY_UP
from .themes import _ThemeType


@dataclass
class ModalOption:
    """An option in a SelectModal."""

    label: str
    description: str = ""
    value: Any = None

    def __post_init__(self) -> None:
        if self.value is None:
            self.value = self.label


@dataclass
class ModalResult:
    """Result from a modal interaction."""

    dismissed: bool  # True if ESC pressed
    confirmed: bool  # True if Enter/y pressed
    value: Any = None  # Selected value or input text


class Modal(ABC):
    """Abstract base class for modal dialogs.

    All modals support:
    - ESC to dismiss (returns dismissed=True)
    - Enter to confirm (returns confirmed=True)
    - Theme-aware styling
    """

    def __init__(
        self,
        title: str,
        theme: _ThemeType,
        box_style: box.Box = box.ROUNDED,
        width: int = 50,
    ) -> None:
        """Initialize modal.

        Args:
            title: Modal title displayed in panel border
            theme: Theme instance for colors
            box_style: Box style for panel border
            width: Minimum width of modal
        """
        self.title = title
        self.theme = theme
        self.box_style = box_style
        self.width = width

    @abstractmethod
    def build(self) -> Panel:
        """Build the modal panel for rendering.

        Returns:
            Rich Panel containing modal content
        """
        pass

    @abstractmethod
    def handle_key(self, key: str) -> Tuple[bool, ModalResult]:
        """Handle a keypress.

        Args:
            key: The key pressed

        Returns:
            Tuple of (should_close, result)
            - should_close: True if modal should be dismissed
            - result: ModalResult with outcome details
        """
        pass


class SelectModal(Modal):
    """Modal with selectable options using radio buttons.

    Navigation:
    - j/k or up/down: Move selection
    - 1-9: Quick select by number
    - Enter: Confirm selection
    - ESC: Cancel
    """

    def __init__(
        self,
        title: str,
        options: List[ModalOption],
        theme: _ThemeType,
        box_style: box.Box = box.ROUNDED,
        width: int = 50,
        selected_index: int = 0,
    ) -> None:
        """Initialize select modal.

        Args:
            title: Modal title
            options: List of ModalOption choices
            theme: Theme instance
            box_style: Panel border style
            width: Minimum width
            selected_index: Initially selected option (0-based)
        """
        super().__init__(title, theme, box_style, width)
        self.options = options
        self.selected_index = min(selected_index, len(options) - 1) if options else 0

    def build(self) -> Panel:
        """Build the select modal panel."""
        content = Text()

        for i, opt in enumerate(self.options):
            # Selection indicator
            if i == self.selected_index:
                indicator = "\u25cf"  # ● filled circle
                style = f"bold {self.theme.info}"
            else:
                indicator = "\u25cb"  # ○ empty circle
                style = self.theme.primary_text

            # Number prefix for quick selection
            num = f"[{i + 1}] " if i < 9 else "    "
            content.append(f"  {num}{indicator} ", style=style)
            content.append(opt.label, style=style)

            # Description on same line if present
            if opt.description:
                content.append("  ", style=self.theme.dim_text)
                content.append(opt.description, style=self.theme.dim_text)

            content.append("\n")

        # Footer with keybinds
        content.append("\n")
        footer = Text()
        footer.append("[Enter]", style=f"bold {self.theme.info}")
        footer.append(" Select  ", style=self.theme.dim_text)
        footer.append("[Esc]", style=f"bold {self.theme.dim_text}")
        footer.append(" Cancel", style=self.theme.dim_text)
        content.append(footer)

        return Panel(
            Align.center(content),
            title=self.title,
            border_style=self.theme.info,
            box=self.box_style,
            width=self.width,
            padding=(1, 2),
        )

    def handle_key(self, key: str) -> Tuple[bool, ModalResult]:
        """Handle keypress for selection."""
        # ESC to cancel
        if key == KEY_ESC:
            return True, ModalResult(dismissed=True, confirmed=False)

        # Enter to confirm
        if key == KEY_ENTER:
            selected = self.options[self.selected_index] if self.options else None
            return True, ModalResult(
                dismissed=False,
                confirmed=True,
                value=selected.value if selected else None,
            )

        # Navigation
        if key in (KEY_UP, "k"):
            self.selected_index = (self.selected_index - 1) % len(self.options)
        elif key in (KEY_DOWN, "j"):
            self.selected_index = (self.selected_index + 1) % len(self.options)

        # Quick select by number (1-9)
        elif key.isdigit() and 1 <= int(key) <= min(9, len(self.options)):
            self.selected_index = int(key) - 1
            selected = self.options[self.selected_index]
            return True, ModalResult(
                dismissed=False,
                confirmed=True,
                value=selected.value,
            )

        return False, ModalResult(dismissed=False, confirmed=False)


class ConfirmModal(Modal):
    """Modal for Yes/No confirmation.

    Navigation:
    - y: Confirm (Yes)
    - n or ESC: Cancel (No)
    - Enter: Confirm highlighted option
    - Left/Right: Toggle highlight
    """

    def __init__(
        self,
        title: str,
        message: str,
        theme: _ThemeType,
        box_style: box.Box = box.ROUNDED,
        width: int = 50,
        danger: bool = False,
        yes_label: str = "Yes",
        no_label: str = "No",
    ) -> None:
        """Initialize confirm modal.

        Args:
            title: Modal title
            message: Confirmation message to display
            theme: Theme instance
            box_style: Panel border style
            width: Minimum width
            danger: If True, use error color for Yes button
            yes_label: Custom label for Yes button
            no_label: Custom label for No button
        """
        super().__init__(title, theme, box_style, width)
        self.message = message
        self.danger = danger
        self.yes_label = yes_label
        self.no_label = no_label
        self.selected_yes = False  # Default to No (safer)

    def build(self) -> Panel:
        """Build the confirm modal panel."""
        content = Text()

        # Message
        content.append(self.message, style=self.theme.primary_text)
        content.append("\n\n")

        # Buttons
        buttons = Text()

        # Yes button
        if self.selected_yes:
            yes_style = f"bold {self.theme.error if self.danger else self.theme.success}"
            buttons.append(f"[{self.yes_label}]", style=yes_style)
        else:
            buttons.append(f" {self.yes_label} ", style=self.theme.dim_text)

        buttons.append("  ")

        # No button
        if not self.selected_yes:
            buttons.append(f"[{self.no_label}]", style=f"bold {self.theme.info}")
        else:
            buttons.append(f" {self.no_label} ", style=self.theme.dim_text)

        content.append(buttons)
        content.append("\n\n")

        # Keybinds
        footer = Text()
        footer.append("[y]", style=f"bold {self.theme.dim_text}")
        footer.append(" Yes  ", style=self.theme.dim_text)
        footer.append("[n]", style=f"bold {self.theme.dim_text}")
        footer.append(" No  ", style=self.theme.dim_text)
        footer.append("[Enter]", style=f"bold {self.theme.dim_text}")
        footer.append(" Confirm", style=self.theme.dim_text)
        content.append(footer)

        border_style = self.theme.error if self.danger else self.theme.info
        return Panel(
            Align.center(content),
            title=self.title,
            border_style=border_style,
            box=self.box_style,
            width=self.width,
            padding=(1, 2),
        )

    def handle_key(self, key: str) -> Tuple[bool, ModalResult]:
        """Handle keypress for confirmation."""
        # Direct yes/no
        if key in ("y", "Y"):
            return True, ModalResult(dismissed=False, confirmed=True, value=True)
        if key in ("n", "N") or key == KEY_ESC:
            return True, ModalResult(dismissed=True, confirmed=False, value=False)

        # Enter confirms current selection
        if key == KEY_ENTER:
            return True, ModalResult(
                dismissed=not self.selected_yes,
                confirmed=self.selected_yes,
                value=self.selected_yes,
            )

        # Left/Right to toggle
        if key in ("h", "l", "\x1b[D", "\x1b[C"):  # h/l or left/right arrows
            self.selected_yes = not self.selected_yes

        return False, ModalResult(dismissed=False, confirmed=False)


@dataclass
class InputValidation:
    """Validation result for input modal."""

    valid: bool
    error_message: str = ""


class InputModal(Modal):
    """Modal for text input with optional validation.

    Navigation:
    - Type: Add characters
    - Backspace: Delete character
    - Ctrl+U: Clear input
    - Enter: Submit (if valid)
    - ESC: Cancel
    """

    def __init__(
        self,
        title: str,
        prompt: str,
        theme: _ThemeType,
        box_style: box.Box = box.ROUNDED,
        width: int = 50,
        initial_value: str = "",
        placeholder: str = "",
        validator: Optional[Callable[[str], InputValidation]] = None,
    ) -> None:
        """Initialize input modal.

        Args:
            title: Modal title
            prompt: Label above input field
            theme: Theme instance
            box_style: Panel border style
            width: Minimum width
            initial_value: Pre-filled text
            placeholder: Placeholder when empty
            validator: Optional validation function
        """
        super().__init__(title, theme, box_style, width)
        self.prompt = prompt
        self.value = initial_value
        self.placeholder = placeholder
        self.validator = validator
        self.error_message = ""

    def build(self) -> Panel:
        """Build the input modal panel."""
        content = Text()

        # Prompt
        content.append(self.prompt, style=self.theme.primary_text)
        content.append("\n\n")

        # Input field
        field_content = Text()
        if self.value:
            field_content.append(self.value, style=self.theme.primary_text)
        else:
            field_content.append(self.placeholder, style=self.theme.dim_text)

        # Cursor
        field_content.append("_", style=f"bold {self.theme.info}")

        # Add field content with visual border styling
        content.append("\n[")
        content.append_text(field_content)
        content.append("]\n")

        # Error message if any
        if self.error_message:
            content.append("\n")
            content.append(self.error_message, style=f"bold {self.theme.error}")

        content.append("\n\n")

        # Footer
        footer = Text()
        footer.append("[Enter]", style=f"bold {self.theme.info}")
        footer.append(" Submit  ", style=self.theme.dim_text)
        footer.append("[Esc]", style=f"bold {self.theme.dim_text}")
        footer.append(" Cancel  ", style=self.theme.dim_text)
        footer.append("[Ctrl+U]", style=f"bold {self.theme.dim_text}")
        footer.append(" Clear", style=self.theme.dim_text)
        content.append(footer)

        # Wrap content with input field visualization
        full_content = Text()
        full_content.append(self.prompt, style=self.theme.primary_text)
        full_content.append("\n\n  ")
        if self.value:
            full_content.append(self.value, style=self.theme.primary_text)
        else:
            full_content.append(self.placeholder, style=self.theme.dim_text)
        full_content.append("_", style=f"bold blink {self.theme.info}")
        full_content.append("\n")

        if self.error_message:
            full_content.append("\n  ")
            full_content.append(self.error_message, style=f"bold {self.theme.error}")

        full_content.append("\n\n")
        full_content.append(footer)

        return Panel(
            Align.center(full_content),
            title=self.title,
            border_style=self.theme.error if self.error_message else self.theme.info,
            box=self.box_style,
            width=self.width,
            padding=(1, 2),
        )

    def handle_key(self, key: str) -> Tuple[bool, ModalResult]:
        """Handle keypress for text input."""
        # ESC to cancel
        if key == KEY_ESC:
            return True, ModalResult(dismissed=True, confirmed=False)

        # Ctrl+U to clear
        if key == "\x15":
            self.value = ""
            self.error_message = ""
            return False, ModalResult(dismissed=False, confirmed=False)

        # Backspace
        if key == KEY_BACKSPACE:
            if self.value:
                self.value = self.value[:-1]
                self.error_message = ""
            return False, ModalResult(dismissed=False, confirmed=False)

        # Enter to submit
        if key == KEY_ENTER:
            # Validate if validator provided
            if self.validator:
                result = self.validator(self.value)
                if not result.valid:
                    self.error_message = result.error_message
                    return False, ModalResult(dismissed=False, confirmed=False)

            return True, ModalResult(
                dismissed=False,
                confirmed=True,
                value=self.value,
            )

        # Printable character
        if len(key) == 1 and key.isprintable():
            self.value += key
            self.error_message = ""

        return False, ModalResult(dismissed=False, confirmed=False)


# Convenience functions for common modals


def create_platform_select_modal(
    theme: _ThemeType,
    box_style: box.Box = box.ROUNDED,
) -> SelectModal:
    """Create a platform selection modal for Start Tracking.

    Returns:
        SelectModal configured with platform options
    """
    options = [
        ModalOption(
            label="Claude Code",
            description="(native tokens)",
            value="claude-code",
        ),
        ModalOption(
            label="Codex CLI",
            description="(tiktoken)",
            value="codex-cli",
        ),
        ModalOption(
            label="Gemini CLI",
            description="(95%+ accuracy)",
            value="gemini-cli",
        ),
    ]
    return SelectModal(
        title="Select Platform",
        options=options,
        theme=theme,
        box_style=box_style,
        width=45,
    )


def create_delete_confirm_modal(
    session_info: str,
    theme: _ThemeType,
    box_style: box.Box = box.ROUNDED,
) -> ConfirmModal:
    """Create a delete confirmation modal.

    Args:
        session_info: Session details to display
        theme: Theme instance

    Returns:
        ConfirmModal configured for deletion
    """
    message = f"Delete this session?\n\n{session_info}\n\nThis action cannot be undone."
    return ConfirmModal(
        title="Delete Session",
        message=message,
        theme=theme,
        box_style=box_style,
        width=50,
        danger=True,
        yes_label="Delete",
        no_label="Cancel",
    )


def create_date_range_input_modal(
    theme: _ThemeType,
    box_style: box.Box = box.ROUNDED,
    initial_value: str = "",
) -> InputModal:
    """Create a date range input modal.

    Args:
        theme: Theme instance
        initial_value: Pre-filled date

    Returns:
        InputModal for date entry
    """

    def validate_date(value: str) -> InputValidation:
        """Validate date format YYYY-MM-DD."""
        if not value:
            return InputValidation(valid=True)
        try:
            from datetime import datetime

            datetime.strptime(value, "%Y-%m-%d")
            return InputValidation(valid=True)
        except ValueError:
            return InputValidation(
                valid=False,
                error_message="Invalid date format. Use YYYY-MM-DD",
            )

    return InputModal(
        title="Date Range",
        prompt="Enter date (YYYY-MM-DD):",
        theme=theme,
        box_style=box_style,
        width=40,
        initial_value=initial_value,
        placeholder="2025-12-26",
        validator=validate_date,
    )
