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
    TerminalResource,
    UIResource,
)
from terminal.glyph import Glyph
from ecs.world import World
from items.components import OnGround
from map.utils import render_map

if TYPE_CHECKING:
    from camera.camera import Camera
    from map.map import GameMap
    from terminal.terminal import GlaiveTerminal
    from ui.state import UIState


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
        look_mode = world.get_resource(LookModeResource)
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
