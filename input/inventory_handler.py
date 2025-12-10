from typing import TYPE_CHECKING, Optional

from ecs.components import Drawable, IsPlayer, Position
from ecs.resources import UIResource
from input.examine_handler import ExamineHandler
from input.input import ActionResult, InputHandler
from items.affixes import ItemAffixes
from items.components import Equipment, Item
from items.equipment import can_equip, equip_item
from items.inventory import drop_item, get_inventory_items
from items.item_types import RARITY_COLORS
from ui.examine import create_examine_popup
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

        # Calculate width based on longest menu item label
        # Format is "x) label" so add 3 for hotkey prefix, plus 4 for border/padding
        max_label_len = max((len(item.label) for item in menu.items), default=10)
        popup_width = max(max_label_len + 7, 20)

        popup: Popup = create_menu_popup(menu, width=popup_width, title="Inventory")

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
                item: Item = self.world.component_for(item_id, Item)
                affixes: ItemAffixes | None = self.world.get_component(
                    item_id, ItemAffixes
                )

                # Build display name with affixes
                if affixes:
                    label = affixes.get_display_name(drawable.name)
                else:
                    label = drawable.name

                # Get rarity color
                color = RARITY_COLORS.get(item.rarity, "white")

                menu.add_item(
                    label,
                    lambda iid=item_id: self._open_item_actions(iid),
                    enabled=True,
                    color=color,
                )

        return menu

    def _open_item_actions(self, item_id: int) -> ActionResult:
        """Open sub-menu with actions for this item"""
        ui_state: UIResource = self.world.resource_for(UIResource)
        drawable: Drawable = self.world.component_for(item_id, Drawable)

        action_menu: Menu = Menu(title=drawable.name)

        # Add "Equip" option if item is equipment
        equipment = self.world.get_component(item_id, Equipment)
        if equipment:
            action_menu.add_item("Equip", lambda: self._equip_item(item_id))

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
        """Show item details in examine popup"""
        ui_state: UIResource = self.world.resource_for(UIResource)

        popup: Popup = create_examine_popup(self.world, item_id)
        handler: ExamineHandler = ExamineHandler(popup, ui_state.popup_stack)

        return ActionResult.push(handler)

    def _equip_item(self, item_id: int) -> ActionResult:
        """Equip item from inventory"""
        ui_state: UIResource = self.world.resource_for(UIResource)
        drawable: Drawable = self.world.component_for(item_id, Drawable)

        players: set[int] = self.world.get_entities_with(IsPlayer)
        player: int = next(iter(players))

        can, reason = can_equip(self.world, player, item_id)
        if can:
            previous: int | None = equip_item(self.world, player, item_id)
            ui_state.message_log.add(f"Equipped {drawable.name}.", "white")
            if previous is not None:
                prev_drawable = self.world.component_for(previous, Drawable)
                ui_state.message_log.add(f"Unequipped {prev_drawable.name}.", "gray")
        else:
            ui_state.message_log.add(f"Cannot equip: {reason}", "red")

        return ActionResult.pop_handler()
