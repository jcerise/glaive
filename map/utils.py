from ecs.world import World
from map.map import TILE_PROPERTIES, GameMap, TileType
from terminal.glyph import Glyph
from terminal.terminal import GlaiveTerminal


def render_map(game_map: GameMap, terminal: GlaiveTerminal, world: World) -> None:
    # Renders a game map onto the terminal. Can render entities as well, from the ECS world
    for y in range(game_map.height):
        for x in range(game_map.width):
            tile_type: TileType = game_map.get_tile(x, y)
            glyph: Glyph = TILE_PROPERTIES[tile_type].glyph

            # Draw map tiles on the lowest level of the terminal
            terminal.draw_glyph(x, y, glyph, 0)
