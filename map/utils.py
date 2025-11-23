from camera.camera import Camera
from ecs.world import World
from map.map import TILE_PROPERTIES, GameMap, TileType
from terminal.glyph import Glyph
from terminal.terminal import GlaiveTerminal


def render_map(
    game_map: GameMap, terminal: GlaiveTerminal, world: World, camera: Camera
) -> None:
    # Renders a game map onto the terminal. Can render entities as well, from the ECS world

    camera_start_x, camera_start_y, camera_end_x, camera_end_y = (
        camera.get_visible_bounds()
    )
    for world_y in range(camera_start_y, camera_end_y):
        for world_x in range(camera_start_x, camera_end_x):
            tile_type: TileType = game_map.get_tile(world_x, world_y)
            glyph: Glyph = TILE_PROPERTIES[tile_type].glyph

            # Check the FOV map, and don't render tiles if they are not currently visible
            if game_map.is_visible(world_x, world_y):
                # Convert world coordinates to screen coordinates prior to drawing
                screen_x, screen_y = camera.world_to_screen(world_x, world_y)

                # Draw map tiles on the lowest level of the terminal, at screen position
                terminal.draw_glyph(screen_x, screen_y, glyph, 0)
