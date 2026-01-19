"""Tests for ESC/POS renderer."""

import pytest

from idea_print.config import PrinterProfile
from idea_print.renderer import (
    ALIGN_CENTER,
    ALIGN_LEFT,
    BOLD_OFF,
    BOLD_ON,
    CUT_FULL,
    INIT,
    Renderer,
    TextBlock,
    feed,
)


class TestRenderer:
    """Tests for the Renderer class."""

    def test_wrap_text_simple(self):
        """Test basic text wrapping."""
        renderer = Renderer(PrinterProfile(chars_per_line=20))
        text = "This is a test of the text wrapping functionality"
        lines = renderer.wrap_text(text)

        assert all(len(line) <= 20 for line in lines)
        assert len(lines) > 1

    def test_wrap_text_preserves_paragraphs(self):
        """Test that double newlines are preserved as paragraph breaks."""
        renderer = Renderer(PrinterProfile(chars_per_line=40))
        text = "First paragraph here.\n\nSecond paragraph here."
        lines = renderer.wrap_text(text)

        # Should have a blank line between paragraphs
        assert "" in lines

    def test_wrap_text_single_newlines(self):
        """Test that single newlines are handled."""
        renderer = Renderer(PrinterProfile(chars_per_line=40))
        text = "Line one\nLine two\nLine three"
        lines = renderer.wrap_text(text)

        assert "Line one" in lines
        assert "Line two" in lines
        assert "Line three" in lines

    def test_wrap_text_long_word(self):
        """Test that long words are NOT broken (overflow instead)."""
        renderer = Renderer(PrinterProfile(chars_per_line=10))
        text = "Supercalifragilisticexpialidocious"
        lines = renderer.wrap_text(text)

        # Long words are kept intact (not broken mid-word)
        assert len(lines) == 1
        assert lines[0] == text

    def test_render_block_basic(self):
        """Test basic text block rendering."""
        renderer = Renderer()
        block = TextBlock(text="Hello World")
        result = renderer.render_block(block)

        assert ALIGN_LEFT in result
        assert b"Hello World" in result
        assert b"\n" in result

    def test_render_block_centered(self):
        """Test centered text block."""
        renderer = Renderer()
        block = TextBlock(text="Centered", align="center")
        result = renderer.render_block(block)

        assert ALIGN_CENTER in result

    def test_render_block_bold(self):
        """Test bold text block."""
        renderer = Renderer()
        block = TextBlock(text="Bold Text", bold=True)
        result = renderer.render_block(block)

        assert BOLD_ON in result
        assert BOLD_OFF in result

    def test_render_complete_document(self):
        """Test complete document rendering."""
        renderer = Renderer()
        blocks = [
            TextBlock(text="Header", align="center", bold=True),
            TextBlock(text="Body text here"),
        ]
        result = renderer.render(blocks)

        # Should start with INIT
        assert result.startswith(INIT)

        # Should end with feed and cut
        assert CUT_FULL in result

    def test_render_line(self):
        """Test horizontal line rendering."""
        renderer = Renderer(PrinterProfile(chars_per_line=20))
        result = renderer.render_line("-")

        assert result == b"-" * 20 + b"\n"

    def test_render_line_custom_char(self):
        """Test horizontal line with custom character."""
        renderer = Renderer(PrinterProfile(chars_per_line=10))
        result = renderer.render_line("=")

        assert result == b"=" * 10 + b"\n"


class TestEscPosCommands:
    """Tests for ESC/POS command constants."""

    def test_init_command(self):
        """Test INIT command bytes."""
        assert INIT == b"\x1b@"

    def test_alignment_commands(self):
        """Test alignment command bytes."""
        assert ALIGN_LEFT == b"\x1ba\x00"
        assert ALIGN_CENTER == b"\x1ba\x01"

    def test_bold_commands(self):
        """Test bold command bytes."""
        assert BOLD_ON == b"\x1bE\x01"
        assert BOLD_OFF == b"\x1bE\x00"

    def test_feed_command(self):
        """Test feed command generation."""
        assert feed(1) == b"\x1bd\x01"
        assert feed(4) == b"\x1bd\x04"

    def test_cut_command(self):
        """Test cut command bytes."""
        assert CUT_FULL == b"\x1dV\x00"
