# ui/menu.py

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Optional, Set

from bearlibterminal import terminal as blt

from input.input import ActionResult, InputHandler
from ui.borders import DEFAULT_BORDER
from ui.popup import Popup, PopupStack
from ui.rect import Rect

if TYPE_CHECKING:
    from ecs.world import World
    from terminal.terminal import GlaiveTerminal


@dataclass
class MenuItem:
    """A single selectable menu item"""

    label: str
    action: Callable[[], ActionResult]
    enabled: bool = True
    # If set, use this key instead of auto-assigning
    hotkey_override: Optional[int] = None


class Menu:
    """
    A keyboard-driven menu with auto-assigned hotkeys (a, b, c...).
    Respects reserved keys from the current input context.
    """

    # All available menu keys in order
    ALL_MENU_KEYS = [
        blt.TK_A,
        blt.TK_B,
        blt.TK_C,
        blt.TK_D,
        blt.TK_E,
        blt.TK_F,
        blt.TK_G,
        blt.TK_H,
        blt.TK_I,
        blt.TK_J,
        blt.TK_K,
        blt.TK_L,
        blt.TK_M,
        blt.TK_N,
        blt.TK_O,
        blt.TK_P,
        blt.TK_Q,
        blt.TK_R,
        blt.TK_S,
        blt.TK_T,
        blt.TK_U,
        blt.TK_V,
        blt.TK_W,
        blt.TK_X,
        blt.TK_Y,
        blt.TK_Z,
    ]

    def __init__(
        self,
        title: Optional[str] = None,
        items: Optional[list[MenuItem]] = None,
        reserved_keys: Optional[Set[int]] = None,
    ):
        """
        Create a menu.

        Args:
            title: Optional title displayed above items
            items: Initial menu items
            reserved_keys: Keys that should NOT be auto-assigned
                          (e.g., keys already bound in the current handler)
        """
        self.title = title
        self.items: list[MenuItem] = items or []
        self.reserved_keys: Set[int] = reserved_keys or set()

        # Escape is always reserved for closing
        self.reserved_keys.add(blt.TK_ESCAPE)

        # Maps key code -> item index
        self._key_to_index: dict[int, int] = {}
        # Maps item index -> key code (for display)
        self._index_to_key: dict[int, int] = {}

        self._rebuild_keybinds()

    def add_item(
        self,
        label: str,
        action: Callable[[], ActionResult],
        enabled: bool = True,
        hotkey: Optional[int] = None,
    ):
        """Add a menu item"""
        item = MenuItem(label, action, enabled, hotkey)
        self.items.append(item)
        self._rebuild_keybinds()
        return self  # Allow chaining

    def set_reserved_keys(self, keys: Set[int]):
        """Update the set of reserved keys and rebuild bindings"""
        self.reserved_keys = keys.copy()
        self.reserved_keys.add(blt.TK_ESCAPE)
        self._rebuild_keybinds()

    def _rebuild_keybinds(self):
        """Rebuild key mappings, skipping reserved keys"""
        self._key_to_index.clear()
        self._index_to_key.clear()

        # Get available keys (not reserved)
        available_keys = [k for k in self.ALL_MENU_KEYS if k not in self.reserved_keys]

        auto_key_idx = 0

        for i, item in enumerate(self.items):
            if item.hotkey_override is not None:
                # Use the override if it's not reserved
                if item.hotkey_override not in self.reserved_keys:
                    self._key_to_index[item.hotkey_override] = i
                    self._index_to_key[i] = item.hotkey_override
            else:
                # Auto-assign from available keys
                if auto_key_idx < len(available_keys):
                    key = available_keys[auto_key_idx]
                    self._key_to_index[key] = i
                    self._index_to_key[i] = key
                    auto_key_idx += 1

    def get_hotkey_char(self, index: int) -> str:
        """Get the display character for a menu item's hotkey"""
        if index in self._index_to_key:
            key = self._index_to_key[index]
            # Convert BLT key code to lowercase letter
            return chr(ord("a") + (key - blt.TK_A))
        return "?"

    def handle_key(self, key: int) -> Optional[ActionResult]:
        """
        Process a key press.
        Returns ActionResult if item was selected, None if key wasn't a menu key.
        """
        if key in self._key_to_index:
            index = self._key_to_index[key]
            item = self.items[index]
            if item.enabled:
                return item.action()
        return None

    def render(self, terminal: "GlaiveTerminal", rect: Rect, layer: int = 4):
        """
        Render the menu within the given rectangle.
        Called by popup's content_renderer.
        """
        y = rect.y

        # Title (if present)
        if self.title:
            terminal.draw_string_at_layer(rect.x, y, self.title, "yellow", layer)
            y += 2

        # Menu items
        for i, item in enumerate(self.items):
            hotkey_char = self.get_hotkey_char(i)

            if item.enabled:
                label_color = "white"
                key_color = "yellow"
            else:
                label_color = "dark gray"
                key_color = "dark gray"

            # Format: "a) Item label"
            key_str = f"{hotkey_char})"
            terminal.draw_string_at_layer(rect.x, y, key_str, key_color, layer)
            terminal.draw_string_at_layer(rect.x + 3, y, item.label, label_color, layer)
            y += 1


class MenuHandler(InputHandler):
    """
    InputHandler wrapper for a Menu.
    Push this onto InputManager when opening a menu.
    Escape always closes the menu.
    """

    def __init__(
        self,
        menu: Menu,
        popup_stack: PopupStack,
        world: "World",
        popup: Optional[Popup] = None,
        parent_handler: Optional[InputHandler] = None,
    ):
        """
        Args:
            menu: The menu to handle
            popup_stack: The popup stack (for pushing/popping the popup)
            world: The game world
            popup: Optional popup to display the menu in
            parent_handler: The handler this menu was opened from
                           (used to get reserved keys)
        """
        self.menu = menu
        self.popup_stack = popup_stack
        self.world = world
        self.popup = popup

        # Get reserved keys from parent handler
        if parent_handler and hasattr(parent_handler, "keybinds"):
            reserved = set(parent_handler.keybinds.keys())
            menu.set_reserved_keys(reserved)

        super().__init__()

    def load_keybinds(self):
        """Escape is bound here; menu items handled in handle_key"""
        self.keybinds = {
            blt.TK_ESCAPE: self._close_menu,
        }

    def handle_key(self, key: int) -> ActionResult:
        # First, check if it's a menu item key
        result = self.menu.handle_key(key)
        if result is not None:
            return result

        # Then check our own keybinds (escape, etc.)
        return super().handle_key(key)

    def _close_menu(self) -> ActionResult:
        """Close this menu and pop its popup"""
        if self.popup and not self.popup_stack.is_empty():
            self.popup_stack.pop()
        return ActionResult.pop_handler()

    def on_enter(self):
        """Called when this handler becomes active"""
        if self.popup:
            self.popup_stack.push(self.popup)

    def on_exit(self):
        """Called when this handler is deactivated"""
        # Popup removal is handled in _close_menu
        pass


def create_menu_popup(
    menu: Menu,
    width: int = 30,
    height: Optional[int] = None,
    title: Optional[str] = None,
) -> Popup:
    """
    Create a popup that displays a menu.

    Args:
        menu: The menu to display
        width: Popup width (including border)
        height: Popup height, or None to auto-calculate
        title: Popup title (defaults to menu title)
    """
    if height is None:
        # Calculate: border(2) + title(2 if present) + items + padding(1)
        title_lines = 2 if menu.title else 0
        height = 2 + title_lines + len(menu.items) + 1

    popup_title = title if title is not None else menu.title

    def render_menu_content(
        popup: Popup, terminal: "GlaiveTerminal", world: "World", layer: int
    ):
        inner = popup.inner_rect
        if inner:
            menu.render(terminal, inner, layer)

    return Popup(
        width=width,
        height=height,
        title=popup_title,
        content_renderer=render_menu_content,
    )
