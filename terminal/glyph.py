from dataclasses import dataclass
from typing import Optional


@dataclass
class Glyph:
    # Represents a single character (object) within the game
    char: str
    fg_color: str
    bg_color: Optional[str] = "black"

    def __post_init__(self):
        # Validate that char is a single character
        if len(self.char) != 1:
            raise ValueError(f"Glyph must be a single character, got: {self.char}")

    def dim(self) -> "Glyph":
        dimmed_color = self._get_dim_color(self.fg_color)
        return Glyph(self.char, dimmed_color, self.bg_color)

    @staticmethod
    def _get_dim_color(color: str) -> str:
        # Map bright colors to their darker equivalents
        dim_map = {
            "white": "gray",
            "light gray": "gray",
            "gray": "dark gray",
            "light blue": "blue",
            "blue": "dark blue",
        }
        return dim_map.get(color, "dark gray")
