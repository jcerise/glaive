from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field

from ui.borders import DEFAULT_BORDER, BorderStyle, draw_border
from ui.log import MessageLog
from ui.rect import Rect

if TYPE_CHECKING:
    from ecs.world import World
    from terminal.terminal import GlaiveTerminal


class Panel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    rect: Rect
    title: Optional[str] = None
    border_style: BorderStyle = Field(default_factory=lambda: DEFAULT_BORDER)

    border_color: str = "white"
    border_layer: int = 2
    content_layer: int = 3

    @property
    def inner_rect(self) -> Rect:
        return self.rect.inner

    def render(self, terminal: "GlaiveTerminal", world: "World"):
        draw_border(
            terminal,
            self.rect,
            self.border_style,
            self.border_color,
            self.title,
            self.border_layer,
        )
        self.render_content(terminal, world)

    def render_content(self, terminal: "GlaiveTerminal", world: "World"):
        pass


class PlayAreaPanel(Panel):
    """
    Main play area panel
    Content is drawn by ECS
    This panel just draws its border, camera handles the rest
    """

    title: Optional[str] = None
    border_color: str = "white"

    def render_content(self, terminal: "GlaiveTerminal", world: "World"):
        pass


class StatsPanel(Panel):
    title: Optional[str] = "Stats"
    border_color: str = "yellow"

    def render_content(self, terminal: "GlaiveTerminal", world: "World"):
        from ecs.components import IsPlayer, Position

        inner: Rect = self.inner_rect

        player_entities: set[int] = world.get_entities_with(IsPlayer)
        if not player_entities:
            return

        player = next(iter(player_entities))

        y: int = inner.y

        terminal.draw_string_at_layer(inner.x, y, "Player", "white", self.content_layer)
        y += 1

        separator: str = "-" * inner.width
        terminal.draw_string_at_layer(
            inner.x, y, separator, "dark gray", self.content_layer
        )
        y += 2

        # Just print the players position for now (we have no stats yet)
        pos = world.get_component(player, Position)
        if pos:
            terminal.draw_string_at_layer(
                inner.x, y, "Position:", "gray", self.content_layer
            )
            y += 1
            terminal.draw_string_at_layer(
                inner.x + 2, y, f"X: {pos.x}", "white", self.content_layer
            )
            y += 1
            terminal.draw_string_at_layer(
                inner.x + 2, y, f"Y: {pos.y}", "white", self.content_layer
            )
            y += 2


class LogPanel(Panel):
    """
    Displays a scrollable log of game messages.
    Shows scroll indicators when not at top/bottom.
    """

    title: Optional[str] = "Log"
    border_color: str = "cyan"
    message_log: "MessageLog"

    def render_content(self, terminal: "GlaiveTerminal", world: "World"):
        inner = self.inner_rect

        visible_lines = inner.height
        messages = self.message_log.get_visible_messages(visible_lines)

        # Draw messages
        for i, (text, color) in enumerate(messages):
            y = inner.y + i
            display_text = text[: inner.width]
            terminal.draw_string_at_layer(
                inner.x, y, display_text, color, self.content_layer
            )

        # Scroll indicators
        if self.message_log.can_scroll_up():
            terminal.draw_string_at_layer(
                self.rect.x2 - 3, self.rect.y, "▲", "yellow", self.border_layer
            )

        if self.message_log.can_scroll_down():
            terminal.draw_string_at_layer(
                self.rect.x2 - 3, self.rect.y2 - 1, "▼", "yellow", self.border_layer
            )
