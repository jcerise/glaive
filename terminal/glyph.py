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
