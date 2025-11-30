from typing import TYPE_CHECKING

from pydantic import BaseModel

from terminal.glyph import Glyph
from ui.rect import Rect

if TYPE_CHECKING:
    from terminal.terminal import GlaiveTerminal


class BorderStyle(BaseModel):
    """
    Defines characters for border drawing
    """

    horizontal: Glyph
    vertical: Glyph
    top_left: Glyph
    top_right: Glyph
    bottom_left: Glyph
    bottom_right: Glyph


DOUBLE_BORDER: BorderStyle = BorderStyle(
    horizontal=Glyph("═", "white"),
    vertical=Glyph("║", "white"),
    top_left=Glyph("╔", "white"),
    top_right=Glyph("╗", "white"),
    bottom_left=Glyph("╚", "white"),
    bottom_right=Glyph("╝", "white"),
)
SINGLE_BORDER: BorderStyle = BorderStyle(
    horizontal=Glyph("─", "white"),
    vertical=Glyph("│", "white"),
    top_left=Glyph("┌", "white"),
    top_right=Glyph("┐", "white"),
    bottom_left=Glyph("└", "white"),
    bottom_right=Glyph("┘", "white"),
)
ASCII_BORDER: BorderStyle = BorderStyle(
    horizontal=Glyph("-", "white"),
    vertical=Glyph("|", "white"),
    top_left=Glyph("+", "white"),
    top_right=Glyph("+", "white"),
    bottom_left=Glyph("+", "white"),
    bottom_right=Glyph("+", "white"),
)

DEFAULT_BORDER = DOUBLE_BORDER


def draw_border(
    terminal: "GlaiveTerminal",
    rect: Rect,
    style: BorderStyle = DEFAULT_BORDER,
    color: str = "white",
    title: str | None = None,
    layer: int = 2,
):
    """
    Draw a border around a rectangle, using the characters defined via BorderStyle
    Can optionally include a centered title in the top border
    """
    # Draw the corners first
    terminal.draw_at_layer(rect.x, rect.y, style.top_left, layer)
    terminal.draw_at_layer(rect.x2 - 1, rect.y, style.top_right, layer)
    terminal.draw_at_layer(rect.x, rect.y2 - 1, style.bottom_left, layer)
    terminal.draw_at_layer(rect.x2 - 1, rect.y2 - 1, style.bottom_right, layer)

    # Next, draw the horizontal edges
    for x in range(rect.x + 1, rect.x2 - 1):
        terminal.draw_at_layer(x, rect.y, style.horizontal, layer)
        terminal.draw_at_layer(x, rect.y2 - 1, style.horizontal, layer)

    # Draw the vertical edges
    for y in range(rect.y + 1, rect.y2 - 1):
        terminal.draw_at_layer(rect.x, y, style.vertical, layer)
        terminal.draw_at_layer(rect.x2 - 1, y, style.vertical, layer)

    # If a title was provided, draw it centered in the top border
    if title:
        title_text: str = f" {title} "
        title_x: int = rect.x + (rect.width - len(title_text)) // 2
        terminal.draw_string_at_layer(title_x, rect.y, title_text, color, layer)


def fill_rect(
    terminal: "GlaiveTerminal",
    rect: Rect,
    char: str = " ",
    fg_color: str = "white",
    bg_color: str = "black",
    layer: int = 2,
):
    """
    Fill a rectangle with a given character. Useful for clearinga rectangle
    """
    for y in range(rect.y, rect.y2):
        glyph: Glyph = Glyph(" ", fg_color, bg_color)
        for x in range(rect.x, rect.x2):
            terminal.draw_at_layer(x, y, glyph, layer)
