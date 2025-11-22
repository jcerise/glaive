from ecs.components import Drawable, IsPlayer, Position, TurnConsumed
from ecs.resources import TerminalResource
from ecs.systems import MovementSystem, RenderSystem, SystemScheduler
from ecs.world import World
from input.handlers import MainGameHandler
from input.input import InputHandler, InputManager
from terminal.terminal import GlaiveTerminal

g_term: GlaiveTerminal = GlaiveTerminal("Glaive", 80, 25)
g_term.init_window()

world: World = World()
world.add_resource(TerminalResource(g_term))

initial_handler: InputHandler = MainGameHandler(world)
input_manager: InputManager = InputManager(initial_handler)

player: int = world.create_entity()
world.add_component(player, IsPlayer())
world.add_component(player, Position(1, 1))
world.add_component(player, Drawable("@", "white", "Player"))

system_scheduler: SystemScheduler = SystemScheduler()
system_scheduler.add_system(RenderSystem(), "render")
system_scheduler.add_system(MovementSystem(), "action")

while True:
    event = g_term.handle_event()

    # If a turn is consumed, the game world will update (enemies move, things happen, etc)
    # If a turn is not consumed, the game world is not updated
    input_manager.process_key(event)
    system_scheduler.update(world)

    turn_consumed: bool = world.get_component(player, TurnConsumed) is not None

    if turn_consumed:
        world.remove_component(player, TurnConsumed)
