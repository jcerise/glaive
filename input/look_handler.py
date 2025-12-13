from typing import TYPE_CHECKING, Optional

from bearlibterminal import terminal as blt

from ecs.components import Drawable, IsActor, IsPlayer, Position
from ecs.resources import LookModeResource, MapResource, UIResource
from input.examine_handler import ExamineHandler
from input.input import ActionResult, InputHandler
from items.components import Item, OnGround
from ui.examine import create_examine_popup
from ui.menu import Menu, MenuHandler, create_menu_popup
from ui.popup import PopupStack

if TYPE_CHECKING:
    from ecs.world import World


class LookHandler(InputHandler):
    """
    Handles look mode - cursor-based map exploration.
    Movement keys move a cursor around the map without consuming turns.
    Shows info about what's at the cursor position.
    """

    def __init__(self, world: "World", popup_stack: PopupStack):
        self.world = world
        self.popup_stack = popup_stack
        self._info_popup: Optional["Popup"] = None

        # Initialize cursor at player position
        players = world.get_entities_with(IsPlayer, Position)
        player = next(iter(players))
        pos: Position = world.component_for(player, Position)

        # Get or create look mode resource
        look_mode = world.get_resource(LookModeResource)
        if look_mode:
            look_mode.cursor_x = pos.x
            look_mode.cursor_y = pos.y
        else:
            world.add_resource(LookModeResource(cursor_x=pos.x, cursor_y=pos.y))

        super().__init__()

    def load_keybinds(self):
        self.keybinds = {
            # Movement - arrow keys
            blt.TK_UP: lambda: self._move_cursor(0, -1),
            blt.TK_DOWN: lambda: self._move_cursor(0, 1),
            blt.TK_LEFT: lambda: self._move_cursor(-1, 0),
            blt.TK_RIGHT: lambda: self._move_cursor(1, 0),
            # Movement - vim keys
            blt.TK_K: lambda: self._move_cursor(0, -1),
            blt.TK_J: lambda: self._move_cursor(0, 1),
            blt.TK_H: lambda: self._move_cursor(-1, 0),
            blt.TK_L: lambda: self._move_cursor(1, 0),
            blt.TK_Y: lambda: self._move_cursor(-1, -1),
            blt.TK_U: lambda: self._move_cursor(1, -1),
            blt.TK_B: lambda: self._move_cursor(-1, 1),
            blt.TK_N: lambda: self._move_cursor(1, 1),
            # Actions
            blt.TK_E: self._examine_at_cursor,
            blt.TK_ESCAPE: self._exit_look,
        }

    def on_enter(self):
        """Activate look mode and show initial info panel"""
        look_mode = self.world.get_resource(LookModeResource)
        look_mode.active = True
        self._update_info_panel()

    def on_exit(self):
        """Deactivate look mode and clean up info panel"""
        look_mode = self.world.get_resource(LookModeResource)
        if look_mode:
            look_mode.active = False
        self._remove_info_panel()

    def _move_cursor(self, dx: int, dy: int) -> ActionResult:
        """Move the look cursor, clamped to map bounds"""
        look_mode = self.world.get_resource(LookModeResource)
        game_map = self.world.resource_for(MapResource)

        new_x = look_mode.cursor_x + dx
        new_y = look_mode.cursor_y + dy

        # Clamp to map bounds
        new_x = max(0, min(new_x, game_map.width - 1))
        new_y = max(0, min(new_y, game_map.height - 1))

        look_mode.cursor_x = new_x
        look_mode.cursor_y = new_y

        self._update_info_panel()
        return ActionResult.no_op()

    def _exit_look(self) -> ActionResult:
        """Exit look mode and return to normal play"""
        self._remove_info_panel()
        return ActionResult.pop_handler()

    def _update_info_panel(self):
        """Update the info panel with current cursor position info"""
        # Remove old panel if present
        self._remove_info_panel()

        # Import here to avoid circular imports
        from ui.look_panel import create_look_info_panel

        look_mode = self.world.get_resource(LookModeResource)
        self._info_popup = create_look_info_panel(
            self.world, look_mode.cursor_x, look_mode.cursor_y
        )
        self.popup_stack.push(self._info_popup)

    def _remove_info_panel(self):
        """Remove the info panel from the popup stack"""
        if self._info_popup and self._info_popup in self.popup_stack._stack:
            self.popup_stack._stack.remove(self._info_popup)
            self._info_popup = None

    def _examine_at_cursor(self) -> ActionResult:
        """Open examine popup for entities at cursor position"""
        look_mode = self.world.get_resource(LookModeResource)
        ui_state = self.world.resource_for(UIResource)

        entities = self._get_entities_at_cursor()

        if not entities:
            ui_state.message_log.add("Nothing to examine here.", "gray")
            return ActionResult.no_op()

        if len(entities) == 1:
            # Single entity - open examine popup directly
            entity_id = entities[0][1]
            popup = create_examine_popup(self.world, entity_id)
            handler = ExamineHandler(popup, self.popup_stack)
            return ActionResult.push(handler)
        else:
            # Multiple entities - show selection menu
            return self._open_entity_selection_menu(entities)

    def _get_entities_at_cursor(self) -> list[tuple[str, int]]:
        """Get all entities at cursor position as (name, entity_id) tuples"""
        look_mode = self.world.get_resource(LookModeResource)
        cx, cy = look_mode.cursor_x, look_mode.cursor_y

        entities: list[tuple[str, int]] = []

        # Get items on ground
        for entity_id in self.world.get_entities_with(OnGround, Position, Item, Drawable):
            pos = self.world.component_for(entity_id, Position)
            if pos.x == cx and pos.y == cy:
                drawable = self.world.component_for(entity_id, Drawable)
                entities.append((drawable.name, entity_id))

        # Get actors (including player)
        for entity_id in self.world.get_entities_with(IsActor, Position, Drawable):
            pos = self.world.component_for(entity_id, Position)
            if pos.x == cx and pos.y == cy:
                drawable = self.world.component_for(entity_id, Drawable)
                entities.append((drawable.name, entity_id))

        return entities

    def _open_entity_selection_menu(
        self, entities: list[tuple[str, int]]
    ) -> ActionResult:
        """Open a menu to select which entity to examine"""
        menu = Menu(title="Examine what?")

        for name, entity_id in entities:
            menu.add_item(name, lambda eid=entity_id: self._examine_entity(eid))

        # Calculate width based on longest name
        max_len = max(len(name) for name, _ in entities)
        popup_width = max(max_len + 7, 20)

        popup = create_menu_popup(menu, width=popup_width)
        handler = MenuHandler(
            menu, self.popup_stack, self.world, popup, parent_handler=self
        )
        return ActionResult.push(handler)

    def _examine_entity(self, entity_id: int) -> ActionResult:
        """Open examine popup for a specific entity"""
        popup = create_examine_popup(self.world, entity_id)
        handler = ExamineHandler(popup, self.popup_stack)
        return ActionResult.push(handler)
