"""Receipt template with ASCII art header and layout."""

from datetime import datetime

from .config import PrinterProfile
from .renderer import (
    ALIGN_CENTER,
    ALIGN_LEFT,
    BOLD_OFF,
    BOLD_ON,
    CUT_FULL,
    CUT_PARTIAL,
    INIT,
    NORMAL_SIZE,
    Renderer,
    TextBlock,
    feed,
)

# ASCII art header - lightbulb design
HEADER_ART = r'''
     .-""-.
    /      \
   |  O  O  |
   |   __   |
    \ \__/ /
     '-..-'
       ||
      /__\
'''

# Simplified header for narrow receipts
HEADER_ART_NARROW = r"""
    .---.
   /     \
  | O   O |
  |  ___  |
   \_____/
     | |
    /___\
"""


def build_receipt(
    idea_text: str,
    idea_id: str | None = None,
    timestamp: datetime | None = None,
    profile: PrinterProfile | None = None,
) -> bytes:
    """Build a complete receipt with header, idea text, and footer."""
    profile = profile or PrinterProfile()
    renderer = Renderer(profile)
    timestamp = timestamp or datetime.now()

    output = bytearray()

    # Initialize
    output.extend(INIT)

    # Header art (centered)
    output.extend(ALIGN_CENTER)
    header = HEADER_ART_NARROW if profile.chars_per_line < 42 else HEADER_ART
    for line in header.strip().split("\n"):
        output.extend(line.encode(profile.encoding, errors="replace"))
        output.extend(b"\n")

    # Blank line
    output.extend(b"\n")

    # Title
    output.extend(BOLD_ON)
    output.extend("NEW IDEA".encode(profile.encoding))
    output.extend(b"\n")
    output.extend(BOLD_OFF)

    # Timestamp
    ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    output.extend(ts_str.encode(profile.encoding))
    output.extend(b"\n")

    # ID if provided
    if idea_id:
        output.extend(f"ID: {idea_id}".encode(profile.encoding))
        output.extend(b"\n")

    output.extend(b"\n")

    # Divider
    output.extend(ALIGN_LEFT)
    output.extend(renderer.render_line("="))

    # Idea text (wrapped)
    lines = renderer.wrap_text(idea_text)
    for line in lines:
        output.extend(line.encode(profile.encoding, errors="replace"))
        output.extend(b"\n")

    # Bottom divider
    output.extend(renderer.render_line("="))

    # Footer
    output.extend(ALIGN_CENTER)
    output.extend(b"\n")
    output.extend("* * *".encode(profile.encoding))
    output.extend(b"\n")

    # Feed and cut
    output.extend(feed(profile.feed_lines_before_cut))

    if profile.cut_type == "full":
        output.extend(CUT_FULL)
    elif profile.cut_type == "partial":
        output.extend(CUT_PARTIAL)

    return bytes(output)


def build_test_receipt(profile: PrinterProfile | None = None) -> bytes:
    """Build a test receipt for printer verification."""
    profile = profile or PrinterProfile()

    return build_receipt(
        idea_text="This is a test print to verify your thermal printer is working correctly. "
        "If you can read this message, the printer is configured properly!",
        idea_id="TEST-001",
        profile=profile,
    )
