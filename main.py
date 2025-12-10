from camera.camera import Camera
from camera.utils import compute_fov
from ecs.components import (
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
from ecs.resources import CameraResource, MapResource, TerminalResource, UIResource
from ecs.systems import (
    MapRenderSystem,
    MovementSystem,
    RenderSystem,
    SystemScheduler,
    UIRenderSystem,
)
from ecs.world import World
from input.handlers import MainGameHandler
from input.input import InputHandler, InputManager
from items.components import Consumable, Equipment, Item, OnGround
from map.generators import ArenaGenerator
from map.map import GameMap
from terminal.glyph import Glyph
from terminal.terminal import GlaiveTerminal
from ui.layout import LayoutManager
from ui.log import MessageLog
from ui.popup import PopupStack
from ui.state import UIState


def create_test_items(world: World):
    """Spawn some test items near player start"""

    # Health potion at (3, 1)
    potion = world.create_entity()
    world.add_component(potion, Item(item_type="consumable", base_value=25))
    world.add_component(potion, Consumable(effect_type="heal", effect_power=20))
    world.add_component(potion, Drawable(Glyph("!", "red"), "Health Potion"))
    world.add_component(potion, Position(3, 1))
    world.add_component(potion, OnGround())

    # Mana potion at (3, 2)
    mana_pot = world.create_entity()
    world.add_component(mana_pot, Item(item_type="consumable", base_value=25))
    world.add_component(
        mana_pot, Consumable(effect_type="restore_mana", effect_power=15)
    )
    world.add_component(mana_pot, Drawable(Glyph("!", "blue"), "Mana Potion"))
    world.add_component(mana_pot, Position(3, 2))
    world.add_component(mana_pot, OnGround())

    # Short sword at (2, 2)
    sword = world.create_entity()
    world.add_component(sword, Item(item_type="equipment", base_value=50))
    world.add_component(sword, Equipment(slot="main_hand", base_damage=5))
    world.add_component(sword, Drawable(Glyph("|", "light gray"), "Short Sword"))
    world.add_component(sword, Position(2, 2))
    world.add_component(sword, OnGround())

    # Dagger at (4, 3)
    dagger = world.create_entity()
    world.add_component(dagger, Item(item_type="equipment", base_value=30))
    world.add_component(dagger, Equipment(slot="main_hand", base_damage=3))
    world.add_component(dagger, Drawable(Glyph("/", "light gray"), "Dagger"))
    world.add_component(dagger, Position(4, 3))
    world.add_component(dagger, OnGround())

    # Leather armor at (5, 2)
    armor = world.create_entity()
    world.add_component(armor, Item(item_type="equipment", base_value=75))
    world.add_component(armor, Equipment(slot="torso", base_defense=3))
    world.add_component(armor, Drawable(Glyph("[", "orange"), "Leather Armor"))
    world.add_component(armor, Position(5, 2))
    world.add_component(armor, OnGround())

    # Iron helmet at (5, 3)
    helmet = world.create_entity()
    world.add_component(helmet, Item(item_type="equipment", base_value=40))
    world.add_component(helmet, Equipment(slot="head", base_defense=2))
    world.add_component(helmet, Drawable(Glyph("^", "light gray"), "Iron Helmet"))
    world.add_component(helmet, Position(5, 3))
    world.add_component(helmet, OnGround())

    # Wooden shield at (6, 2)
    shield = world.create_entity()
    world.add_component(shield, Item(item_type="equipment", base_value=35))
    world.add_component(shield, Equipment(slot="off_hand", base_defense=2))
    world.add_component(shield, Drawable(Glyph(")", "orange"), "Wooden Shield"))
    world.add_component(shield, Position(6, 2))
    world.add_component(shield, OnGround())

    # Leather boots at (6, 3)
    boots = world.create_entity()
    world.add_component(boots, Item(item_type="equipment", base_value=25))
    world.add_component(boots, Equipment(slot="feet", base_defense=1))
    world.add_component(boots, Drawable(Glyph("[", "orange"), "Leather Boots"))
    world.add_component(boots, Position(6, 3))
    world.add_component(boots, OnGround())

    # Silver ring at (7, 2)
    ring = world.create_entity()
    world.add_component(ring, Item(item_type="equipment", base_value=60))
    world.add_component(
        ring, Equipment(slot="ring", base_defense=0)
    )  # Will add stat bonuses later
    world.add_component(ring, Drawable(Glyph("=", "light gray"), "Silver Ring"))
    world.add_component(ring, Position(7, 2))
    world.add_component(ring, OnGround())

    # Gold necklace at (7, 3)
    necklace = world.create_entity()
    world.add_component(necklace, Item(item_type="equipment", base_value=80))
    world.add_component(necklace, Equipment(slot="necklace", base_defense=0))
    world.add_component(necklace, Drawable(Glyph('"', "yellow"), "Gold Necklace"))
    world.add_component(necklace, Position(7, 3))
    world.add_component(necklace, OnGround())

    # Cloak at (8, 2)
    cape = world.create_entity()
    world.add_component(cape, Item(item_type="equipment", base_value=45))
    world.add_component(cape, Equipment(slot="cape", base_defense=1))
    world.add_component(cape, Drawable(Glyph("(", "dark green"), "Traveler's Cloak"))
    world.add_component(cape, Position(8, 2))
    world.add_component(cape, OnGround())

    # Gold coins at (1, 2)
    gold = world.create_entity()
    world.add_component(gold, Item(item_type="treasure", base_value=10))
    world.add_component(gold, Drawable(Glyph("$", "yellow"), "Gold Coins"))
    world.add_component(gold, Position(1, 2))
    world.add_component(gold, OnGround())

    # Ruby at (8, 3)
    ruby = world.create_entity()
    world.add_component(ruby, Item(item_type="treasure", base_value=100))
    world.add_component(ruby, Drawable(Glyph("*", "red"), "Ruby"))
    world.add_component(ruby, Position(8, 3))
    world.add_component(ruby, OnGround())


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

world: World = World()
world.add_resource(TerminalResource(g_term))
world.add_resource(CameraResource(camera))
world.add_resource(UIResource(ui_state))

initial_handler: InputHandler = MainGameHandler(world)
input_manager: InputManager = InputManager(initial_handler)

player: int = world.create_entity()
world.add_component(player, IsPlayer())
world.add_component(player, IsActor())
world.add_component(player, Position(1, 1))
world.add_component(player, Drawable(Glyph("@", "white"), "Player"))
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
