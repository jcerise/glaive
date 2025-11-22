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

        return game_map
