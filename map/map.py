from dataclasses import dataclass
from enum import Enum

from terminal.glyph import Glyph


class TileType(Enum):
    FLOOR = 0
    WALL = 1
    SHALLOW_WATER = 2
    DEEP_WATER = 3
    ABYSS = 4


@dataclass
class TileProperties:
    blocks_movement: bool
    blocks_sight: bool
    movement_cost: int
    glyph: Glyph


TILE_PROPERTIES = {
    TileType.FLOOR: TileProperties(False, False, 1, Glyph(".", "gray")),
    TileType.WALL: TileProperties(True, True, 0, Glyph("#", "dark gray")),
    TileType.SHALLOW_WATER: TileProperties(False, False, 2, Glyph("~", "light blue")),
    TileType.DEEP_WATER: TileProperties(True, False, 3, Glyph("~", "dark blue")),
    TileType.ABYSS: TileProperties(True, False, 0, Glyph(".", "light gray")),
}


class GameMap:
    def __init__(self, width: int, height: int):
        self.width: int = width
        self.height: int = height
        # Initialize map to all walls
        self.tiles: list[list[TileType]] = [
            [TileType.FLOOR for _ in range(width)] for _ in range(height)
        ]

    def get_tile(self, x: int, y: int) -> TileType:
        return self.tiles[y][x]

    def set_tile(self, x: int, y: int, tile_type: TileType) -> None:
        self.tiles[y][x] = tile_type

    def blocks_movement(self, x: int, y: int) -> bool:
        # Any location outside of the bounds of the map should always block movement
        if not self.in_bounds(x, y):
            return False

        return TILE_PROPERTIES[self.get_tile(x, y)].blocks_movement

    def blocks_sight(self, x: int, y: int) -> bool:
        return TILE_PROPERTIES[self.get_tile(x, y)].blocks_sight

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height
