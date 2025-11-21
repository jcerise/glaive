from ecs.components import Drawable, Position
from ecs.resources import TerminalResource
from ecs.world import World
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
        for phase_name, _ in self.phases:
            for system in self.phases[phase_name]:
                system.update(world)


class RenderSystem(System):
    def update(self, world: World) -> None:
        terminal: GlaiveTerminal = world.resource_for(TerminalResource)
        for entity in world.get_entities_with(Position, Drawable):
            pos_component: Position = world.component_for(entity, Position)
            drawable_component: Drawable = world.component_for(entity, Drawable)

            terminal.draw(
                pos_component.x,
                pos_component.y,
                drawable_component.char,
                drawable_component.color,
            )
