"""ESC/POS byte generation and text processing."""

import textwrap
from dataclasses import dataclass
from typing import Literal

from .config import PrinterProfile

# ESC/POS command bytes
ESC = b"\x1b"
GS = b"\x1d"

# Initialization
INIT = ESC + b"@"  # ESC @ - Initialize printer

# Text alignment
ALIGN_LEFT = ESC + b"a\x00"  # ESC a 0
ALIGN_CENTER = ESC + b"a\x01"  # ESC a 1
ALIGN_RIGHT = ESC + b"a\x02"  # ESC a 2

# Text formatting
BOLD_ON = ESC + b"E\x01"  # ESC E 1
BOLD_OFF = ESC + b"E\x00"  # ESC E 0
UNDERLINE_ON = ESC + b"-\x01"  # ESC - 1
UNDERLINE_OFF = ESC + b"-\x00"  # ESC - 0

# Double size
DOUBLE_HEIGHT_ON = ESC + b"!\x10"  # ESC ! 16
DOUBLE_WIDTH_ON = ESC + b"!\x20"  # ESC ! 32
DOUBLE_SIZE_ON = ESC + b"!\x30"  # ESC ! 48
NORMAL_SIZE = ESC + b"!\x00"  # ESC ! 0

# Line feed
def feed(n: int) -> bytes:
    """Generate feed command for n lines."""
    return ESC + b"d" + bytes([n])


# Paper cutting
CUT_FULL = GS + b"V\x00"  # GS V 0 - Full cut
CUT_PARTIAL = GS + b"V\x01"  # GS V 1 - Partial cut


Alignment = Literal["left", "center", "right"]


@dataclass
class TextBlock:
    """A block of text with formatting."""

    text: str
    bold: bool = False
    align: Alignment = "left"
    double_height: bool = False
    double_width: bool = False


class Renderer:
    """Renders text blocks to ESC/POS bytes."""

    def __init__(self, profile: PrinterProfile | None = None):
        self.profile = profile or PrinterProfile()

    def wrap_text(self, text: str) -> list[str]:
        """Wrap text to fit printer width, preserving paragraphs."""
        width = self.profile.chars_per_line
        lines: list[str] = []

        # Split on double newlines to preserve paragraphs
        paragraphs = text.split("\n\n")

        for i, paragraph in enumerate(paragraphs):
            # Handle single newlines within paragraph
            sub_paragraphs = paragraph.split("\n")
            for sub in sub_paragraphs:
                sub = sub.strip()
                if not sub:
                    lines.append("")
                else:
                    wrapped = textwrap.wrap(
                        sub,
                        width=width,
                        break_long_words=False,
                        break_on_hyphens=False,
                    )
                    lines.extend(wrapped if wrapped else [""])

            # Add blank line between paragraphs (but not after last)
            if i < len(paragraphs) - 1:
                lines.append("")

        return lines

    def render_alignment(self, align: Alignment) -> bytes:
        """Get alignment command bytes."""
        if align == "center":
            return ALIGN_CENTER
        elif align == "right":
            return ALIGN_RIGHT
        return ALIGN_LEFT

    def render_block(self, block: TextBlock) -> bytes:
        """Render a text block to ESC/POS bytes."""
        output = bytearray()

        # Set alignment
        output.extend(self.render_alignment(block.align))

        # Set formatting
        if block.bold:
            output.extend(BOLD_ON)

        if block.double_height and block.double_width:
            output.extend(DOUBLE_SIZE_ON)
        elif block.double_height:
            output.extend(DOUBLE_HEIGHT_ON)
        elif block.double_width:
            output.extend(DOUBLE_WIDTH_ON)

        # Wrap and encode text
        effective_width = self.profile.chars_per_line
        if block.double_width:
            effective_width //= 2

        lines = textwrap.wrap(
            block.text,
            width=effective_width,
            break_long_words=False,
            break_on_hyphens=False,
        ) if block.text.strip() else [block.text]

        for line in lines:
            output.extend(line.encode(self.profile.encoding, errors="replace"))
            output.extend(b"\n")

        # Reset formatting
        if block.bold:
            output.extend(BOLD_OFF)

        if block.double_height or block.double_width:
            output.extend(NORMAL_SIZE)

        return bytes(output)

    def render(self, blocks: list[TextBlock]) -> bytes:
        """Render multiple text blocks to a complete ESC/POS document."""
        output = bytearray()

        # Initialize printer
        output.extend(INIT)

        # Render each block
        for block in blocks:
            output.extend(self.render_block(block))

        # Feed paper and cut
        output.extend(feed(self.profile.feed_lines_before_cut))

        if self.profile.cut_type == "full":
            output.extend(CUT_FULL)
        elif self.profile.cut_type == "partial":
            output.extend(CUT_PARTIAL)

        return bytes(output)

    def render_line(self, char: str = "-") -> bytes:
        """Render a horizontal line across the receipt."""
        line = char * self.profile.chars_per_line
        return line.encode(self.profile.encoding) + b"\n"

    def render_blank_lines(self, count: int = 1) -> bytes:
        """Render blank lines."""
        return b"\n" * count
