from ecs.components import Drawable, MoveIntent, Position, TurnConsumed
from ecs.resources import MapResource, TerminalResource
from ecs.world import World
from map.map import GameMap
from terminal.terminal import GlaiveTerminal


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
        terminal: GlaiveTerminal = world.resource_for(TerminalResource)
        for entity in world.get_entities_with(Position, Drawable):
            pos_component: Position = world.component_for(entity, Position)
            drawable_component: Drawable = world.component_for(entity, Drawable)

            # Draw entities on layer 1 of the terminal (above map tiles on layer 0)
            terminal.draw_glyph(
                pos_component.x, pos_component.y, drawable_component.glyph, 1
            )


class MovementSystem(System):
    def update(self, world: World) -> None:
        game_map: GameMap = world.resource_for(MapResource)
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

    def try_move(self, new_x: int, new_y: int, game_map: GameMap) -> bool:
        # Check the game map, and ensure the tile the user wants to move to does not block movement
        if not game_map.blocks_movement(new_x, new_y):
            self.x = new_x
            self.y = new_y
            return True

        return False
