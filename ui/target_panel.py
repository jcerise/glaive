"""Target mode state for tile-based targeting (throwing, spells, etc.)."""

from dataclasses import dataclass


@dataclass
class TargetMode:
    """
    Tracks the state of tile-based targeting.

    Used by TargetHandler for throwing items, using scrolls, etc.
    The TargetCursorRenderSystem reads this to render the targeting UI.
    """

    active: bool = False
    cursor_x: int = 0
    cursor_y: int = 0
    origin_x: int = 0  # Where the targeting started (usually player position)
    origin_y: int = 0
    max_range: int = 5
    radius: int = 0  # AoE radius, 0 for single target
    show_path: bool = False  # Show trajectory line to cursor
