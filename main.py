from camera.camera import Camera
from camera.utils import compute_fov
from ecs.components import (
    Description,
    Drawable,
    EquipmentSlots,
    Experience,
    Health,
    Inventory,
    IsActor,
    IsPlayer,
    Mana,
    Position,
    Stats,
    TurnConsumed,
)
from ecs.resources import (
    CameraResource,
    LookModeResource,
    MapResource,
    TerminalResource,
    UIResource,
)
from ecs.systems import (
    LookCursorRenderSystem,
    MapRenderSystem,
    MovementSystem,
    RenderSystem,
    SystemScheduler,
    UIRenderSystem,
)
from ecs.world import World
from input.handlers import MainGameHandler
from input.input import InputHandler, InputManager
from items.factory import (
    create_armor,
    create_consumable,
    create_treasure,
    create_weapon,
)
from map.generators import ArenaGenerator
from map.map import GameMap
from terminal.glyph import Glyph
from terminal.terminal import GlaiveTerminal
from ui.layout import LayoutManager
from ui.log import MessageLog
from ui.look_panel import LookMode
from ui.popup import PopupStack
from ui.state import UIState


def create_test_items(world: World):
    """Spawn test items with various rarities near player start"""

    create_consumable(world, "Health Potion", "!", "red", "heal", 20, 25, 3, 1)
    create_consumable(world, "Mana Potion", "!", "blue", "restore_mana", 15, 25, 3, 2)

    # Common sword - no affixes (white)
    create_weapon(
        world,
        "Short Sword",
        "|",
        "light gray",
        "main_hand",
        5,
        50,
        2,
        2,
        rarity="common",
    )
    # Uncommon dagger - one affix (green)
    create_weapon(
        world, "Dagger", "/", "light gray", "main_hand", 3, 30, 4, 3, rarity="uncommon"
    )
    # Rare longsword - both prefix and suffix (light blue)
    create_weapon(
        world, "Longsword", "|", "light gray", "main_hand", 7, 100, 9, 2, rarity="rare"
    )

    # Common leather armor - no affixes (white)
    create_armor(
        world, "Leather Armor", "[", "orange", "torso", 3, 75, 5, 2, rarity="common"
    )
    # Uncommon helmet - one affix (green)
    create_armor(
        world, "Iron Helmet", "^", "light gray", "head", 2, 40, 5, 3, rarity="uncommon"
    )
    # Rare shield - both prefix and suffix (light blue)
    create_armor(
        world, "Tower Shield", ")", "light gray", "off_hand", 4, 80, 6, 2, rarity="rare"
    )
    # Random rarity boots
    create_armor(world, "Leather Boots", "[", "orange", "feet", 1, 25, 6, 3)
    # Random rarity ring
    create_armor(world, "Silver Ring", "=", "light gray", "ring", 0, 60, 7, 2)
    # Random rarity necklace
    create_armor(world, "Gold Necklace", '"', "yellow", "necklace", 0, 80, 7, 3)
    # Random rarity cape
    create_armor(world, "Traveler's Cloak", "(", "dark green", "cape", 1, 45, 8, 2)

    create_treasure(world, "Gold Coins", "$", "yellow", "gold", 10, 1, 2)
    create_treasure(world, "Ruby", "*", "red", "gem", 100, 8, 3)


g_term: GlaiveTerminal = GlaiveTerminal("Glaive", 80, 25)
g_term.init_window()

# Create our UI components
message_log: MessageLog = MessageLog()
layout: LayoutManager = LayoutManager(80, 25, message_log)
popup_stack: PopupStack = PopupStack(80, 25)

ui_state: UIState = UIState(layout, popup_stack, message_log)

play_area = layout.get_play_area_inner()
camera: Camera = Camera(play_area.width, play_area.height, 160, 50)
camera.set_screen_offset(play_area.x, play_area.y)

# Instantiate a look mode resource
look_mode: LookMode = LookMode()

world: World = World()
world.add_resource(TerminalResource(g_term))
world.add_resource(CameraResource(camera))
world.add_resource(UIResource(ui_state))
world.add_resource(LookModeResource(look_mode))

initial_handler: InputHandler = MainGameHandler(world)
input_manager: InputManager = InputManager(initial_handler)

player: int = world.create_entity()
world.add_component(player, IsPlayer())
world.add_component(player, IsActor())
world.add_component(player, Position(1, 1))
world.add_component(player, Drawable(Glyph("@", "white"), "Player"))
world.add_component(player, Description("Yourself, a brave adventurer."))
world.add_component(player, Stats())  # Default stats (all 10s)
world.add_component(player, Health(current_hp=30))
world.add_component(player, Mana(current_mp=15))
world.add_component(player, Experience())
world.add_component(player, Inventory(max_slots=20))
world.add_component(player, EquipmentSlots())

# Create a few items laying around to test inventory, and inventory actions
create_test_items(world)

# Update the camera with the players position, to initialize its location
camera.update(1, 1)

system_scheduler: SystemScheduler = SystemScheduler()
system_scheduler.add_system(MapRenderSystem(), "render")
system_scheduler.add_system(RenderSystem(), "render")
system_scheduler.add_system(LookCursorRenderSystem(), "render")
system_scheduler.add_system(UIRenderSystem(), "render")
system_scheduler.add_system(MovementSystem(), "action")

# Create a basic Arena map, that takes up the terminal (no camera yet)
arena_generator: ArenaGenerator = ArenaGenerator(160, 50)
game_map: GameMap = arena_generator.generate()
world.add_resource(MapResource(game_map))

# Add a few initial system messages
message_log.add("Welcome to Glaive!", "yellow")
message_log.add("Use arrow keys or hjklyubn to move.", "gray")

# Initial render
g_term.clear()
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
    compute_fov(game_map, player_pos.x, player_pos.y)

    g_term.refresh()
