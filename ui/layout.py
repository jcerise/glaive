from typing import TYPE_CHECKING

from ui.panel import LogPanel, Panel, PlayAreaPanel, StatsPanel
from ui.rect import Rect

if TYPE_CHECKING:
    from ecs.world import World
    from terminal.terminal import GlaiveTerminal
    from ui.log import MessageLog


class LayoutManager:
    """
    Manages the three main panels and their layout.
    """

    def __init__(
        self, screen_width: int, screen_height: int, message_log: "MessageLog"
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.message_log = message_log

        # Calculate panel dimensions
        stats_width = screen_width // 4
        stats_x = screen_width - stats_width
        left_width = screen_width - stats_width
        log_height = screen_height // 4
        play_height = screen_height - log_height

        # Create panels with Pydantic models
        self.play_panel = PlayAreaPanel(
            rect=Rect(x=0, y=0, width=left_width, height=play_height)
        )

        self.stats_panel = StatsPanel(
            rect=Rect(x=stats_x, y=0, width=stats_width, height=screen_height)
        )

        self.log_panel = LogPanel(
            rect=Rect(x=0, y=play_height, width=left_width, height=log_height),
            message_log=message_log,
        )

        self.panels: list[Panel] = [self.play_panel, self.stats_panel, self.log_panel]

    def get_play_area_inner(self) -> Rect:
        """Get the inner rectangle of the play area for camera sizing"""
        return self.play_panel.inner_rect

    def get_play_area_offset(self) -> tuple[int, int]:
        """Get the screen offset for the play area"""
        inner = self.play_panel.inner_rect
        return (inner.x, inner.y)

    def render_panels(self, terminal: "GlaiveTerminal", world: "World"):
        """Render all panel borders and their content"""
        for panel in self.panels:
            panel.render(terminal, world)
