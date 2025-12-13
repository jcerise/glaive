from bearlibterminal import terminal

from ecs.components import Drawable, IsPlayer, MoveIntent, Position
from ecs.resources import UIResource
from ecs.world import World
from input.equipment_handler import EquipmentHandler
from input.input import ActionResult, InputHandler
from input.inventory_handler import InventoryHandler
from input.look_handler import LookHandler
from items.components import Equipment
from items.inventory import can_pickup, get_items_at_position, pickup_item
from ui.menu import Menu, MenuHandler, Popup, create_menu_popup


class MainGameHandler(InputHandler):
    def __init__(self, world: World):
        super().__init__()
        self.world: World = world

    def load_keybinds(self):
        self.keybinds = {
            # Movement - arrow keys
            terminal.TK_UP: self.move_north,
            terminal.TK_DOWN: self.move_south,
            terminal.TK_LEFT: self.move_west,
            terminal.TK_RIGHT: self.move_east,
            # Movement - vim keys
            terminal.TK_K: self.move_north,
            terminal.TK_J: self.move_south,
            terminal.TK_H: self.move_west,
            terminal.TK_L: self.move_east,
            terminal.TK_Y: self.move_northwest,
            terminal.TK_U: self.move_northeast,
            terminal.TK_B: self.move_southwest,
            terminal.TK_N: self.move_southeast,
            # TODO: Actions
            terminal.TK_G: self.pickup_item,
            terminal.TK_I: self.open_inventory,
            terminal.TK_E: self.open_equipment,
            terminal.TK_M: self.open_main_menu,
            terminal.TK_X: self.start_look_mode,
            # 'c': self.start_cast_spell,
            # 't': self.start_throw,
            # 'L': self.start_look_mode,  # Capital L for look
            # 'a': self.start_interact,
            # '.': self.wait,
            # ',': self.pickup_item,  # Alternative
        }

    def move_north(self) -> ActionResult:
        return self._move(0, -1)

    def move_south(self) -> ActionResult:
        return self._move(0, 1)

    def move_west(self) -> ActionResult:
        return self._move(-1, 0)

    def move_east(self) -> ActionResult:
        return self._move(1, 0)

    def move_northwest(self) -> ActionResult:
        return self._move(-1, -1)

    def move_northeast(self) -> ActionResult:
        return self._move(1, -1)

    def move_southwest(self) -> ActionResult:
        return self._move(-1, 1)

    def move_southeast(self) -> ActionResult:
        return self._move(1, 1)

    def _move(self, dx: int, dy: int) -> ActionResult:
        players = self.world.get_entities_with(IsPlayer)
        player: int = next(iter(players))
        self.world.add_component(player, MoveIntent(dx, dy, True))

        return ActionResult.no_op()

    def open_main_menu(self) -> ActionResult:
        ui_state = self.world.resource_for(UIResource)

        # Create menu
        menu = Menu(title="Menu")
        menu.add_item("Inventory", self.open_inventory)
        menu.add_item("Character", self._not_implemented)
        menu.add_item("Options", self._not_implemented)
        menu.add_item("Help", self._show_help)
        menu.add_item("Quit", self._quit_game)

        # Create popup for the menu
        popup = create_menu_popup(menu, width=25)

        # Create handler (passes self so menu knows which keys to avoid)
        handler = MenuHandler(
            menu, ui_state.popup_stack, self.world, popup, parent_handler=self
        )

        return ActionResult.push(handler)

    def open_inventory(self) -> ActionResult:
        ui_state: UIResource = self.world.resource_for(UIResource)
        handler = InventoryHandler(
            self.world, ui_state.popup_stack, parent_handler=self
        )
        return ActionResult.push(handler)

    def pickup_item(self) -> ActionResult:
        """Pick up item(s) at player's feet"""
        ui_state: UIResource = self.world.resource_for(UIResource)

        players: set[int] = self.world.get_entities_with(IsPlayer)
        player: int = next(iter(players))
        pos: Position = self.world.component_for(player, Position)

        items: list[int] = get_items_at_position(self.world, pos.x, pos.y)

        if not items:
            ui_state.message_log.add("Nothing here to pick up.", "gray")
            return ActionResult.no_op()

        if len(items) == 1:
            # Single item - pick it up directly
            item_id: int = items[0]
            drawable: Drawable = self.world.component_for(item_id, Drawable)

            if can_pickup(self.world, player, item_id):
                pickup_item(self.world, player, item_id)
                ui_state.message_log.add(f"Picked up {drawable.name}.", "white")
            else:
                ui_state.message_log.add("Inventory is full.", "red")
            return ActionResult.no_op()
        else:
            # Multiple items - open pickup menu
            return self._open_pickup_menu(items)

    def _open_pickup_menu(self, items: list[int]) -> ActionResult:
        """Open menu to select which item to pick up"""
        ui_state: UIResource = self.world.resource_for(UIResource)

        menu: Menu = Menu(title="Pick up")
        for item_id in items:
            drawable: Drawable = self.world.component_for(item_id, Drawable)
            menu.add_item(drawable.name, lambda iid=item_id: self._do_pickup(iid))

        popup: Popup = create_menu_popup(menu, width=35)
        handler: MenuHandler = MenuHandler(
            menu, ui_state.popup_stack, self.world, popup, parent_handler=self
        )
        return ActionResult.push(handler)

    def _do_pickup(self, item_id: int) -> ActionResult:
        """Actually pick up the selected item"""
        ui_state: UIResource = self.world.resource_for(UIResource)

        players: set[int] = self.world.get_entities_with(IsPlayer)
        player: int = next(iter(players))
        drawable: Drawable = self.world.component_for(item_id, Drawable)

        if can_pickup(self.world, player, item_id):
            pickup_item(self.world, player, item_id)
            ui_state.message_log.add(f"Picked up {drawable.name}.", "white")
        else:
            ui_state.message_log.add("Inventory is full.", "red")

        return ActionResult.pop_handler()

    def open_equipment(self) -> ActionResult:
        ui_state: UIResource = self.world.resource_for(UIResource)
        handler: EquipmentHandler = EquipmentHandler(
            self.world, ui_state.popup_stack, parent_handler=self
        )
        return ActionResult.push(handler)

    def start_look_mode(self) -> ActionResult:
        ui_state: UIResource = self.world.resource_for(UIResource)
        handler: LookHandler = LookHandler(self.world, ui_state.popup_stack)
        return ActionResult.push(handler)

    def _not_implemented(self) -> ActionResult:
        ui_state = self.world.resource_for(UIResource)
        ui_state.message_log.add("Not yet implemented.", "gray")
        return ActionResult.no_op()  # Close menu after showing message

    def _show_help(self) -> ActionResult:
        # Could open another popup with help text
        ui_state = self.world.resource_for(UIResource)
        ui_state.message_log.add("Press arrow keys or hjklyubn to move.", "white")
        ui_state.message_log.add("Press M for menu, I for inventory.", "white")
        return ActionResult.no_op()

    def _quit_game(self) -> ActionResult:
        terminal.close()
        exit()
