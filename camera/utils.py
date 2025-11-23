import tcod
from tcod import libtcodpy

from map.map import GameMap


def compute_fov(
    game_map: GameMap, player_x: int, player_y: int, radius: int = 8
) -> None:
    game_map.clear_visible()

    transparency: list[list[bool]] = game_map.get_transparency_map()

    visible_tiles = tcod.map.compute_fov(
        transparency=transparency,
        pov=(player_x, player_y),
        radius=radius,
        light_walls=True,
        algorithm=libtcodpy.FOV_SYMMETRIC_SHADOWCAST,
    )

    for y in range(game_map.height):
        for x in range(game_map.width):
            if visible_tiles[x, y]:
                game_map.set_visible(x, y, True)
