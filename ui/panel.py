from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field

from ui.borders import DEFAULT_BORDER, BorderStyle, draw_border
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
