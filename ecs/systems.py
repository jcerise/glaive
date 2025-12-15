from typing import TYPE_CHECKING, Optional

from ecs.components import (
    Drawable,
    IsActor,
    IsPlayer,
    MoveIntent,
    Position,
    TurnConsumed,
)
from ecs.resources import (
    CameraResource,
    LookModeResource,
    MapResource,
    TargetModeResource,
    TerminalResource,
    UIResource,
)
from ecs.world import World
from effects.components import GroundPool
from items.components import OnGround
from map.utils import render_map
from terminal.glyph import Glyph

if TYPE_CHECKING:
    from camera.camera import Camera
    from map.map import GameMap
    from terminal.terminal import GlaiveTerminal
    from ui.look_panel import LookMode
    from ui.state import UIState
    from ui.target_panel import TargetMode


class System:
    def update(self, world: World) -> None:
        raise NotImplementedError


class SystemScheduler:
    def __init__(self):
        self.phases: dict[str, list[System]] = {
            "input": [],
            "ai": [],
            "action": [],
            "resolution": [],
            "cleanup": [],
            "render": [],
        }

    def add_system(self, system: System, phase: str) -> None:
        self.phases[phase].append(system)

    def update(self, world: World) -> None:
        for phase_name in self.phases:
            for system in self.phases[phase_name]:
                system.update(world)


class RenderSystem(System):
    def update(self, world: World) -> None:
        terminal: "GlaiveTerminal" = world.resource_for(TerminalResource)
        camera: "Camera" = world.resource_for(CameraResource)
        game_map: "GameMap" = world.resource_for(MapResource)

        # Render items on the ground first
        for entity in world.get_entities_with(Position, Drawable, OnGround):
            pos_component: Position = world.component_for(entity, Position)
            drawable_component: Drawable = world.component_for(entity, Drawable)

            if camera.is_visible(
                pos_component.x, pos_component.y
            ) and game_map.is_visible(pos_component.x, pos_component.y):
                screen_x, screen_y = camera.world_to_screen(
                    pos_component.x, pos_component.y
                )
                terminal.draw_at_layer(screen_x, screen_y, drawable_component.glyph, 1)

        # Then render any actors (player, monsters, etc)
        for entity in world.get_entities_with(Position, Drawable, IsActor):
            pos_component: Position = world.component_for(entity, Position)
            drawable_component: Drawable = world.component_for(entity, Drawable)
            player_component: Optional[IsPlayer] = world.get_component(entity, IsPlayer)

            # Only draw entities that are visible to the camera
            if (
                camera.is_visible(pos_component.x, pos_component.y)
                and game_map.is_visible(pos_component.x, pos_component.y)
            ) or player_component:
                # Convert entity world coordinates to screen coordinates, so they properly draw in the camera
                screen_x, screen_y = camera.world_to_screen(
                    pos_component.x, pos_component.y
                )
                # Draw entities on layer 1 of the terminal (above map tiles on layer 0)
                terminal.draw_at_layer(screen_x, screen_y, drawable_component.glyph, 1)


class LookCursorRenderSystem(System):
    """
    Renders the look mode cursor ('X') when look mode is active.
    Should run after RenderSystem, before UIRenderSystem.
    """

    def update(self, world: World) -> None:
        look_mode: "LookMode" = world.resource_for(LookModeResource)
        if not look_mode or not look_mode.active:
            return

        terminal: "GlaiveTerminal" = world.resource_for(TerminalResource)
        camera: "Camera" = world.resource_for(CameraResource)

        # Check if cursor is visible on screen
        if not camera.is_visible(look_mode.cursor_x, look_mode.cursor_y):
            return

        # Transform to screen coordinates
        screen_x, screen_y = camera.world_to_screen(
            look_mode.cursor_x, look_mode.cursor_y
        )

        # Draw 'X' cursor on layer 2 (above entities on layer 1)
        terminal.draw_at_layer(screen_x, screen_y, Glyph("X", "yellow"), 2)


class TargetCursorRenderSystem(System):
    """
    Renders the targeting cursor and range indicator when target mode is active.
    Shows valid range, path preview, and AoE radius.
    Should run after RenderSystem, before UIRenderSystem.
    """

    def update(self, world: World) -> None:
        target_mode: "TargetMode" = world.resource_for(TargetModeResource)
        if not target_mode.active:
            return

        terminal: "GlaiveTerminal" = world.resource_for(TerminalResource)
        camera: "Camera" = world.resource_for(CameraResource)
        game_map: "GameMap" = world.resource_for(MapResource)

        # Import here to avoid circular imports
        from effects.targeting import get_line, has_line_of_sight, is_in_range

        # Draw range indicator (subtle highlight on valid tiles)
        for dy in range(-target_mode.max_range, target_mode.max_range + 1):
            for dx in range(-target_mode.max_range, target_mode.max_range + 1):
                tx = target_mode.origin_x + dx
                ty = target_mode.origin_y + dy

                if not game_map.in_bounds(tx, ty):
                    continue
                if not camera.is_visible(tx, ty):
                    continue

                # Skip the origin tile
                if tx == target_mode.origin_x and ty == target_mode.origin_y:
                    continue

                screen_x, screen_y = camera.world_to_screen(tx, ty)

                in_range = is_in_range(
                    target_mode.origin_x,
                    target_mode.origin_y,
                    tx,
                    ty,
                    target_mode.max_range,
                )
                if in_range:
                    # Check line of sight
                    has_los = has_line_of_sight(
                        target_mode.origin_x,
                        target_mode.origin_y,
                        tx,
                        ty,
                        game_map,
                    )
                    # In range with LoS - green dot, blocked - dark gray dot
                    color = "dark green" if has_los else "darker gray"
                    terminal.draw_at_layer(screen_x, screen_y, Glyph(".", color), 2)

        # Draw path preview if enabled
        if target_mode.show_path:
            path = get_line(
                target_mode.origin_x,
                target_mode.origin_y,
                target_mode.cursor_x,
                target_mode.cursor_y,
            )
            # Skip origin and cursor, draw path between
            for px, py in path[1:-1]:
                if camera.is_visible(px, py):
                    screen_x, screen_y = camera.world_to_screen(px, py)
                    terminal.draw_at_layer(screen_x, screen_y, Glyph("*", "yellow"), 2)

        # Draw AoE radius preview if applicable
        if target_mode.radius > 0:
            cursor_in_range = is_in_range(
                target_mode.origin_x,
                target_mode.origin_y,
                target_mode.cursor_x,
                target_mode.cursor_y,
                target_mode.max_range,
            )
            if cursor_in_range:
                for dy in range(-target_mode.radius, target_mode.radius + 1):
                    for dx in range(-target_mode.radius, target_mode.radius + 1):
                        tx = target_mode.cursor_x + dx
                        ty = target_mode.cursor_y + dy

                        if not game_map.in_bounds(tx, ty):
                            continue

                        # Use Chebyshev distance for radius
                        dist = max(abs(dx), abs(dy))
                        if dist <= target_mode.radius and dist > 0:
                            if camera.is_visible(tx, ty):
                                screen_x, screen_y = camera.world_to_screen(tx, ty)
                                terminal.draw_at_layer(
                                    screen_x, screen_y, Glyph("*", "orange"), 2
                                )

        # Draw cursor last (on top of everything)
        if camera.is_visible(target_mode.cursor_x, target_mode.cursor_y):
            screen_x, screen_y = camera.world_to_screen(
                target_mode.cursor_x, target_mode.cursor_y
            )

            # Color based on validity (range and line of sight)
            cursor_in_range = is_in_range(
                target_mode.origin_x,
                target_mode.origin_y,
                target_mode.cursor_x,
                target_mode.cursor_y,
                target_mode.max_range,
            )
            cursor_has_los = has_line_of_sight(
                target_mode.origin_x,
                target_mode.origin_y,
                target_mode.cursor_x,
                target_mode.cursor_y,
                game_map,
            )
            cursor_valid = cursor_in_range and cursor_has_los
            cursor_color = "green" if cursor_valid else "red"
            terminal.draw_at_layer(screen_x, screen_y, Glyph("X", cursor_color), 2)


class UIRenderSystem(System):
    """
    Renders the UI layer: panels and popups.
    Should run AFTER the game's RenderSystem.
    """

    def update(self, world: World) -> None:
        terminal: "GlaiveTerminal" = world.resource_for(TerminalResource)
        ui_state: "UIState" = world.resource_for(UIResource)

        # 1. Render panel borders and content (stats, log)
        ui_state.layout_manager.render_panels(terminal, world)

        # 2. Render popup stack (if any popups are open)
        ui_state.popup_stack.render(terminal, world)


class MovementSystem(System):
    def update(self, world: World) -> None:
        game_map: "GameMap" = world.resource_for(MapResource)
        for entity in world.get_entities_with(MoveIntent, Position):
            intent: MoveIntent = world.component_for(entity, MoveIntent)
            pos: Position = world.component_for(entity, Position)

            new_x: int = pos.x + intent.dx
            new_y: int = pos.y + intent.dy

            if self.try_move(new_x, new_y, game_map):
                pos.x = new_x
                pos.y = new_y

                if intent.consumes_turn:
                    world.add_component(entity, TurnConsumed())

            world.remove_component(entity, MoveIntent)

    def try_move(self, new_x: int, new_y: int, game_map: "GameMap") -> bool:
        # Check the game map, and ensure the tile the user wants to move to does not block movement
        if not game_map.blocks_movement(new_x, new_y):
            self.x = new_x
            self.y = new_y
            return True

        return False


class MapRenderSystem(System):
    """
    Renders the map layer
    This always gets drawn at the lowest level of the terminal (0)
    """

    def update(self, world: World) -> None:
        terminal: "GlaiveTerminal" = world.resource_for(TerminalResource)
        game_map: "GameMap" = world.resource_for(MapResource)
        camera: "Camera" = world.resource_for(CameraResource)

        render_map(game_map, terminal, world, camera)


class PoolRenderSystem(System):
    """
    Renders ground pools (from thrown potions, etc.)
    Renders on layer 1, same as items but before them.
    """

    def update(self, world: World) -> None:
        terminal: "GlaiveTerminal" = world.resource_for(TerminalResource)
        camera: "Camera" = world.resource_for(CameraResource)
        game_map: "GameMap" = world.resource_for(MapResource)

        for entity in world.get_entities_with(Position, Drawable, GroundPool):
            pos = world.component_for(entity, Position)
            drawable = world.component_for(entity, Drawable)

            if camera.is_visible(pos.x, pos.y) and game_map.is_visible(pos.x, pos.y):
                screen_x, screen_y = camera.world_to_screen(pos.x, pos.y)
                terminal.draw_at_layer(screen_x, screen_y, drawable.glyph, 1)
