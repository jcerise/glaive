from map.map import GameMap, TileType


class BaseGenerator:
    def __init__(self, width: int, height: int):
        self.width: int = width
        self.height: int = height

    def generate(self) -> GameMap:
        raise NotImplementedError


class ArenaGenerator(BaseGenerator):
    # Generates a single large room, surrounded by walls
    # Best for testing mechanics
    def generate(self) -> GameMap:
        game_map: GameMap = GameMap(self.width, self.height)

        # Fill wall in on the boundaries of the map, and the rest is floor
        for y in range(self.height):
            for x in range(self.width):
                if x == 0 or y == 0 or x == self.width - 1 or y == self.height - 1:
                    game_map.set_tile(x, y, TileType.WALL)
                else:
                    game_map.set_tile(x, y, TileType.FLOOR)

        # Second pass to fill in some pillars (for testing FoV and pathfinding)
        pillar_spacing: int = 8
        for pillar_y in range(pillar_spacing, self.height - 2, pillar_spacing):
            for pillar_x in range(pillar_spacing, self.width - 2, pillar_spacing):
                # Draw a 2x2 pillar of wall
                for dy in range(2):
                    for dx in range(2):
                        game_map.set_tile(pillar_x + dx, pillar_y + dy, TileType.WALL)

        return game_map
