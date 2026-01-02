#!/usr/bin/env python3
"""
Regression tests for v1.0.4 bug fixes (task-245).

Tests cover:
- task-245.1: Platform name normalization (codex-cli -> codex_cli)
- task-245.2: Help modal 'q' key behavior (should close modal, not quit TUI)

These tests ensure previously fixed bugs don't regress.
"""

import pytest

from token_audit.cli import normalize_platform
from token_audit.display.session_browser import BrowserMode, SessionBrowser


class TestPlatformNormalization:
    """Tests for task-245.1: Platform name normalization fix."""

    def test_normalize_claude_code(self) -> None:
        """CLI hyphen format should normalize to internal underscore format."""
        assert normalize_platform("claude-code") == "claude_code"

    def test_normalize_codex_cli(self) -> None:
        """CLI hyphen format should normalize to internal underscore format."""
        assert normalize_platform("codex-cli") == "codex_cli"

    def test_normalize_gemini_cli(self) -> None:
        """CLI hyphen format should normalize to internal underscore format."""
        assert normalize_platform("gemini-cli") == "gemini_cli"

    def test_normalize_none(self) -> None:
        """None should pass through unchanged."""
        assert normalize_platform(None) is None

    def test_normalize_auto(self) -> None:
        """'auto' should return None (auto means 'all platforms' / no filter)."""
        assert normalize_platform("auto") is None

    def test_normalize_already_underscore(self) -> None:
        """Already underscore format should remain unchanged."""
        assert normalize_platform("claude_code") == "claude_code"
        assert normalize_platform("codex_cli") == "codex_cli"
        assert normalize_platform("gemini_cli") == "gemini_cli"


class TestHelpModalQKey:
    """Tests for task-245.2: Help modal 'q' key behavior fix."""

    def test_q_in_help_mode_returns_false(self) -> None:
        """Pressing 'q' in help mode should NOT quit TUI (return False)."""
        browser = SessionBrowser()
        browser.state.mode = BrowserMode.HELP

        # 'q' should return False (stay in app), not True (quit)
        result = browser._handle_help_key("q")
        assert result is False, "q in help mode should return False (not quit)"

    def test_q_in_help_mode_closes_help(self) -> None:
        """Pressing 'q' in help mode should close the help overlay."""
        browser = SessionBrowser()
        browser.state.mode = BrowserMode.HELP

        browser._handle_help_key("q")
        assert browser.state.mode == BrowserMode.LIST, "q should close help overlay"

    def test_capital_q_in_help_mode(self) -> None:
        """Pressing 'Q' in help mode should also close help, not quit."""
        browser = SessionBrowser()
        browser.state.mode = BrowserMode.HELP

        result = browser._handle_help_key("Q")
        assert result is False, "Q in help mode should return False (not quit)"
        assert browser.state.mode == BrowserMode.LIST, "Q should close help overlay"

    def test_escape_in_help_mode(self) -> None:
        """Pressing Escape in help mode should close help overlay."""
        browser = SessionBrowser()
        browser.state.mode = BrowserMode.HELP

        result = browser._handle_help_key("escape")
        assert result is False
        assert browser.state.mode == BrowserMode.LIST

    def test_q_only_quits_in_list_mode(self) -> None:
        """Verify 'q' only quits TUI when in list mode (not help)."""
        browser = SessionBrowser()
        browser.state.mode = BrowserMode.LIST

        # In list mode, 'q' should quit
        result = browser._handle_key("q")
        assert result is True, "q in list mode should quit TUI"
