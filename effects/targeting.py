from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from map.map import GameMap


def get_distance(x1: int, y1: int, x2: int, y2: int) -> float:
    """Calculate Euclidean distance between two points."""
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def get_chebyshev_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """
    Calculate Chebyshev distance (diagonal movement costs 1).
    This is the standard roguelike distance metric.
    """
    return max(abs(x2 - x1), abs(y2 - y1))


def is_in_range(
    origin_x: int, origin_y: int, target_x: int, target_y: int, max_range: int
) -> bool:
    """Check if target is within range of origin using Chebyshev distance."""
    return get_chebyshev_distance(origin_x, origin_y, target_x, target_y) <= max_range


def get_line(x1: int, y1: int, x2: int, y2: int) -> list[tuple[int, int]]:
    """
    Bresenham's line algorithm - returns all points from (x1,y1) to (x2,y2).
    Used for projectile paths and line-of-sight checks.
    """
    points: list[tuple[int, int]] = []

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    x, y = x1, y1
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1

    if dx > dy:
        err = dx / 2
        while x != x2:
            points.append((x, y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2
        while y != y2:
            points.append((x, y))
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy

    points.append((x2, y2))
    return points


def get_tiles_in_radius(
    center_x: int, center_y: int, radius: int, game_map: "GameMap"
) -> list[tuple[int, int]]:
    """
    Get all tiles within radius of center, clamped to map bounds.
    Uses Chebyshev distance (square radius).
    """
    tiles: list[tuple[int, int]] = []

    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if get_chebyshev_distance(0, 0, dx, dy) <= radius:
                tx, ty = center_x + dx, center_y + dy
                if game_map.in_bounds(tx, ty):
                    tiles.append((tx, ty))

    return tiles


def has_line_of_sight(x1: int, y1: int, x2: int, y2: int, game_map: "GameMap") -> bool:
    """
    Check if there's a clear line of sight between two points.
    Returns False if any tile along the line blocks sight.
    """
    line = get_line(x1, y1, x2, y2)

    # Check all tiles except start and end
    for x, y in line[1:-1]:
        if game_map.blocks_sight(x, y):
            return False

    return True
