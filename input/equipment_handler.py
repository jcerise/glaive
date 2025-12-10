from typing import TYPE_CHECKING, Optional

from ecs.components import Drawable, EquipmentSlots, IsPlayer
from ecs.resources import UIResource
from input.examine_handler import ExamineHandler
from input.input import ActionResult, InputHandler
from items.affixes import ItemAffixes
from items.components import Item
from items.equipment import (
    SLOT_DISPLAY_NAMES,
    SLOT_DISPLAY_ORDER,
    unequip_to_inventory,
)
from items.item_types import RARITY_COLORS
from ui.examine import create_examine_popup
from ui.menu import Menu, MenuHandler, create_menu_popup
from ui.popup import Popup, PopupStack

if TYPE_CHECKING:
    from ecs.world import World


class EquipmentHandler(MenuHandler):
    """
    Handles equipment screen popup.
    Shows all equipment slots and allows unequipping items.
    """

    def __init__(
        self,
        world: "World",
        popup_stack: PopupStack,
        parent_handler: Optional[InputHandler] = None,
    ):
        self.world = world
        self._parent_handler = parent_handler

        menu: Menu = self._build_equipment_menu()

        # Calculate width based on longest menu item label
        # Format is "x) label" so add 3 for hotkey prefix, plus 4 for border/padding
        max_label_len = max((len(item.label) for item in menu.items), default=10)
        popup_width = max(max_label_len + 7, 20)

        popup: Popup = create_menu_popup(menu, width=popup_width, title="Equipment")

        super().__init__(menu, popup_stack, world, popup, parent_handler)

    def _build_equipment_menu(self) -> Menu:
        """Build menu showing all equipment slots"""
        menu: Menu = Menu(title=None)

        players: set[int] = self.world.get_entities_with(IsPlayer)
        if not players:
            return menu
        player: int = next(iter(players))

        equip_slots: EquipmentSlots = self.world.component_for(player, EquipmentSlots)
        if not equip_slots:
            menu.add_item(
                "(no equipment slots)", lambda: ActionResult.no_op(), enabled=False
            )
            return menu

        for slot in SLOT_DISPLAY_ORDER:
            item_id = equip_slots.slots.get(slot)
            slot_name = SLOT_DISPLAY_NAMES.get(slot, slot)

            if item_id is not None:
                drawable = self.world.component_for(item_id, Drawable)
                item: Item = self.world.component_for(item_id, Item)
                affixes: ItemAffixes | None = self.world.get_component(
                    item_id, ItemAffixes
                )

                # Build display name with affixes
                if affixes:
                    item_name = affixes.get_display_name(drawable.name)
                else:
                    item_name = drawable.name

                label = f"{slot_name}: {item_name}"
                color = RARITY_COLORS.get(item.rarity, "white")

                menu.add_item(
                    label,
                    lambda s=slot, iid=item_id: self._open_slot_actions(s, iid),
                    enabled=True,
                    color=color,
                )
            else:
                label = f"{slot_name}: (empty)"
                menu.add_item(label, lambda: ActionResult.no_op(), enabled=False)

        return menu

    def _open_slot_actions(self, slot: str, item_id: int) -> ActionResult:
        """Open sub-menu with actions for equipped item"""
        ui_state: UIResource = self.world.resource_for(UIResource)
        drawable: Drawable = self.world.component_for(item_id, Drawable)

        action_menu: Menu = Menu(title=drawable.name)
        action_menu.add_item("Unequip", lambda: self._unequip_item(slot, item_id))
        action_menu.add_item("Examine", lambda: self._examine_item(item_id))

        popup: Popup = create_menu_popup(action_menu, width=25)
        handler: MenuHandler = MenuHandler(
            action_menu, ui_state.popup_stack, self.world, popup, parent_handler=self
        )

        return ActionResult.push(handler)

    def _unequip_item(self, slot: str, item_id: int) -> ActionResult:
        """Unequip item and move to inventory"""
        ui_state: UIResource = self.world.resource_for(UIResource)
        drawable: Drawable = self.world.component_for(item_id, Drawable)

        players: set[int] = self.world.get_entities_with(IsPlayer)
        player: int = next(iter(players))

        result: int | None = unequip_to_inventory(self.world, player, slot)
        if result is not None:
            ui_state.message_log.add(f"Unequipped {drawable.name}.", "white")
        else:
            ui_state.message_log.add("Inventory is full.", "red")

        return ActionResult.pop_handler()

    def _examine_item(self, item_id: int) -> ActionResult:
        """Show equipment details in examine popup"""
        ui_state: UIResource = self.world.resource_for(UIResource)

        popup: Popup = create_examine_popup(self.world, item_id)
        handler: ExamineHandler = ExamineHandler(popup, ui_state.popup_stack)

        return ActionResult.push(handler)
