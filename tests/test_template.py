"""Tests for receipt template."""

from datetime import datetime

import pytest

from idea_print.config import PrinterProfile
from idea_print.renderer import CUT_FULL, INIT
from idea_print.template import HEADER_ART, HEADER_ART_NARROW, build_receipt, build_test_receipt


class TestBuildReceipt:
    """Tests for build_receipt function."""

    def test_basic_receipt(self):
        """Test building a basic receipt."""
        result = build_receipt(
            idea_text="This is my brilliant idea",
            idea_id="IDEA-001",
        )

        # Should be bytes
        assert isinstance(result, bytes)

        # Should start with INIT
        assert result.startswith(INIT)

        # Should contain the idea text
        assert b"This is my brilliant idea" in result

        # Should contain the ID
        assert b"IDEA-001" in result

        # Should end with cut
        assert CUT_FULL in result

    def test_receipt_without_id(self):
        """Test receipt without idea ID."""
        result = build_receipt(idea_text="Just the idea")

        assert b"Just the idea" in result
        assert b"ID:" not in result

    def test_receipt_with_timestamp(self):
        """Test receipt with specific timestamp."""
        ts = datetime(2024, 6, 15, 14, 30, 0)
        result = build_receipt(
            idea_text="Timestamped idea",
            timestamp=ts,
        )

        assert b"2024-06-15 14:30:00" in result

    def test_receipt_narrow_profile(self):
        """Test receipt with narrow printer profile."""
        profile = PrinterProfile(chars_per_line=32)
        result = build_receipt(
            idea_text="Narrow receipt",
            profile=profile,
        )

        # Should use narrow header
        assert isinstance(result, bytes)
        # Receipt should still be valid
        assert result.startswith(INIT)

    def test_receipt_long_text_wrapping(self):
        """Test that long text is properly wrapped."""
        long_text = (
            "This is a very long idea that should be wrapped across multiple "
            "lines because it exceeds the width of the thermal printer paper. "
            "The text wrapping should preserve readability."
        )
        result = build_receipt(idea_text=long_text)

        # Should contain the text (possibly wrapped)
        assert b"This is a very long idea" in result

    def test_receipt_special_characters(self):
        """Test handling of special characters."""
        result = build_receipt(idea_text="Caf\u00e9 & restaurant ideas!")

        # Should handle encoding (may replace unknown chars)
        assert isinstance(result, bytes)


class TestBuildTestReceipt:
    """Tests for build_test_receipt function."""

    def test_test_receipt_generated(self):
        """Test that test receipt is generated."""
        result = build_test_receipt()

        assert isinstance(result, bytes)
        assert result.startswith(INIT)
        assert b"TEST-001" in result
        assert b"test print" in result.lower()

    def test_test_receipt_with_profile(self):
        """Test test receipt with custom profile."""
        profile = PrinterProfile(chars_per_line=32)
        result = build_test_receipt(profile=profile)

        assert isinstance(result, bytes)


class TestHeaderArt:
    """Tests for ASCII art headers."""

    def test_header_art_exists(self):
        """Test that header art is defined."""
        assert HEADER_ART
        assert HEADER_ART_NARROW

    def test_header_art_is_string(self):
        """Test header art is string."""
        assert isinstance(HEADER_ART, str)
        assert isinstance(HEADER_ART_NARROW, str)

    def test_narrow_header_is_narrower(self):
        """Test that narrow header fits in smaller width."""
        narrow_max = max(len(line) for line in HEADER_ART_NARROW.strip().split("\n"))
        wide_max = max(len(line) for line in HEADER_ART.strip().split("\n"))

        assert narrow_max <= wide_max
