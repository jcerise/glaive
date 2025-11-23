from camera.camera import Camera
from ecs.components import Drawable, IsPlayer, Position, TurnConsumed
from ecs.resources import CameraResource, MapResource, TerminalResource
from ecs.systems import MovementSystem, RenderSystem, SystemScheduler
from ecs.world import World
from input.handlers import MainGameHandler
from input.input import InputHandler, InputManager
from map.generators import ArenaGenerator
from map.map import GameMap
from map.utils import render_map
from terminal.glyph import Glyph
from terminal.terminal import GlaiveTerminal

g_term: GlaiveTerminal = GlaiveTerminal("Glaive", 80, 25)
g_term.init_window()

camera: Camera = Camera(80, 25, 160, 50)

world: World = World()
world.add_resource(TerminalResource(g_term))
world.add_resource(CameraResource(camera))

initial_handler: InputHandler = MainGameHandler(world)
input_manager: InputManager = InputManager(initial_handler)

player: int = world.create_entity()
world.add_component(player, IsPlayer())
world.add_component(player, Position(1, 1))
world.add_component(player, Drawable(Glyph("@", "white"), "Player"))

# Update the camera with the players position, to initialize its location
camera.update(1, 1)

system_scheduler: SystemScheduler = SystemScheduler()
system_scheduler.add_system(RenderSystem(), "render")
system_scheduler.add_system(MovementSystem(), "action")

# Create a basic Arena map, that takes up the terminal (no camera yet)
arena_generator: ArenaGenerator = ArenaGenerator(160, 50)
game_map: GameMap = arena_generator.generate()
world.add_resource(MapResource(game_map))

# Initial render
g_term.clear()
render_map(game_map, g_term, world, camera)
system_scheduler.update(world)
g_term.refresh()

while True:
    g_term.clear()
    event = g_term.handle_event()

    # If a turn is consumed, the game world will update (enemies move, things happen, etc)
    # If a turn is not consumed, the game world is not updated
    input_manager.process_key(event)
    system_scheduler.update(world)

    turn_consumed: bool = world.get_component(player, TurnConsumed) is not None

    if turn_consumed:
        world.remove_component(player, TurnConsumed)

    # Finally, update the camera and render the map
    player_pos: Position = world.component_for(player, Position)
    camera.update(player_pos.x, player_pos.y)
    render_map(game_map, g_term, world, camera)

    g_term.refresh()
