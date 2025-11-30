from typing import TYPE_CHECKING, Callable, Optional

from pydantic import BaseModel, ConfigDict, Field

from ui.borders import DEFAULT_BORDER, BorderStyle, draw_border, fill_rect
from ui.rect import Rect

if TYPE_CHECKING:
    from ecs.world import World
    from terminal.terminal import GlaiveTerminal


class Popup(BaseModel):
    """
    A floating popup window that appears centered on screen.
    Renders above all panels. Game world still renders underneath.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    width: int
    height: int
    title: Optional[str] = None
    border_style: BorderStyle = Field(default_factory=lambda: DEFAULT_BORDER)
    border_color: str = "white"
    bg_color: str = "black"
    content_renderer: Optional[
        Callable[["Popup", "GlaiveTerminal", "World", int], None]
    ] = None

    # Private, set during render
    _rect: Optional[Rect] = None

    def get_rect(self, screen_width: int, screen_height: int) -> Rect:
        """Calculate centered position on screen"""
        return Rect.centered(screen_width, screen_height, self.width, self.height)

    @property
    def rect(self) -> Optional[Rect]:
        """The popup's screen rectangle (set after first render)"""
        return self._rect

    @property
    def inner_rect(self) -> Optional[Rect]:
        """The content area inside the border"""
        if self._rect:
            return self._rect.inner
        return None

    def render(
        self,
        terminal: "GlaiveTerminal",
        world: "World",
        screen_width: int,
        screen_height: int,
        layer: int,
    ):
        """Render the popup at the specified layer"""
        # Calculate centered position
        self._rect = self.get_rect(screen_width, screen_height)

        # Fill background
        fill_rect(terminal, self._rect, " ", self.bg_color, self.bg_color, layer)

        # Draw border
        draw_border(
            terminal,
            self._rect,
            self.border_style,
            self.border_color,
            self.title,
            layer,
        )

        # Render custom content
        if self.content_renderer:
            self.content_renderer(self, terminal, world, layer)


class PopupStack:
    """
    Manages a stack of popup windows.
    Popups render in order (bottom of stack first, top last).
    """

    BASE_LAYER = 4

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self._stack: list[Popup] = []

    def push(self, popup: Popup):
        """Add a popup to the top of the stack"""
        self._stack.append(popup)

    def pop(self) -> Optional[Popup]:
        """Remove and return the top popup"""
        if self._stack:
            return self._stack.pop()
        return None

    def peek(self) -> Optional[Popup]:
        """Get the top popup without removing it"""
        if self._stack:
            return self._stack[-1]
        return None

    def is_empty(self) -> bool:
        return len(self._stack) == 0

    def clear(self):
        self._stack.clear()

    @property
    def depth(self) -> int:
        return len(self._stack)

    def render(self, terminal: "GlaiveTerminal", world: "World"):
        """Render all popups in stack order"""
        for i, popup in enumerate(self._stack):
            layer = self.BASE_LAYER + i
            popup.render(terminal, world, self.screen_width, self.screen_height, layer)


from ecs.world import World
from terminal.terminal import GlaiveTerminal

Popup.model_rebuild()
