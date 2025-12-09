from typing import TYPE_CHECKING, Optional

from ecs.components import Drawable, IsPlayer, Position
from ecs.resources import UIResource
from input.input import ActionResult, InputHandler
from items.components import Item
from items.inventory import drop_item, get_inventory_items
from ui.menu import Menu, MenuHandler, create_menu_popup
from ui.popup import Popup, PopupStack

if TYPE_CHECKING:
    from ecs.world import World


class InventoryHandler(MenuHandler):
    """
    Handles inventory popup with item-specific actions.
    Selecting an item opens a sub-menu with actions (drop, examine, etc.)
    """

    def __init__(
        self,
        world: "World",
        popup_stack: PopupStack,
        parent_handler: Optional[InputHandler] = None,
    ):
        self.world = world
        self._parent_handler = parent_handler

        menu: Menu = self._build_inventory_menu()
        popup: Popup = create_menu_popup(menu, width=40, title="Inventory")

        super().__init__(menu, popup_stack, world, popup, parent_handler)

    def _build_inventory_menu(self) -> Menu:
        """Build menu from player's actual inventory"""
        menu: Menu = Menu(title=None)

        players: set[int] = self.world.get_entities_with(IsPlayer)
        if not players:
            return menu
        player: int = next(iter(players))

        items: list[int] = get_inventory_items(self.world, player)

        if not items:
            # Empty inventory - add a disabled placeholder
            menu.add_item("(empty)", lambda: ActionResult.no_op(), enabled=False)
        else:
            for item_id in items:
                drawable = self.world.component_for(item_id, Drawable)

                label = drawable.name

                menu.add_item(
                    label,
                    lambda iid=item_id: self._open_item_actions(iid),
                    enabled=True,
                )

        return menu

    def _open_item_actions(self, item_id: int) -> ActionResult:
        """Open sub-menu with actions for this item"""
        ui_state: UIResource = self.world.resource_for(UIResource)
        drawable: Drawable = self.world.component_for(item_id, Drawable)

        action_menu: Menu = Menu(title=drawable.name)
        action_menu.add_item("Drop", lambda: self._drop_item(item_id))
        action_menu.add_item("Examine", lambda: self._examine_item(item_id))

        popup: Popup = create_menu_popup(action_menu, width=25)
        handler: MenuHandler = MenuHandler(
            action_menu, ui_state.popup_stack, self.world, popup, parent_handler=self
        )

        return ActionResult.push(handler)

    def _drop_item(self, item_id: int) -> ActionResult:
        """Drop item at player's feet"""
        ui_state: UIResource = self.world.resource_for(UIResource)

        players: set[int] = self.world.get_entities_with(IsPlayer)
        player: int = next(iter(players))
        pos: Position = self.world.component_for(player, Position)
        drawable: Drawable = self.world.component_for(item_id, Drawable)

        if drop_item(self.world, player, item_id, pos.x, pos.y):
            ui_state.message_log.add(f"Dropped {drawable.name}.", "white")
        else:
            ui_state.message_log.add(f"Couldn't drop the {drawable.name}", "red")

        # Close both menus (action menu + inventory)
        # Pop action menu, then refresh inventory
        return ActionResult.pop_handler()

    def _examine_item(self, item_id: int) -> ActionResult:
        """Show item details in message log"""
        ui_state: UIResource = self.world.resource_for(UIResource)
        drawable: Drawable = self.world.component_for(item_id, Drawable)
        item: Item = self.world.component_for(item_id, Item)

        ui_state.message_log.add(f"{drawable.name}", "yellow")
        ui_state.message_log.add(f"  Type: {item.item_type}", "gray")
        ui_state.message_log.add(f"  Value: {item.base_value} gold", "gray")

        return ActionResult.pop_handler()
