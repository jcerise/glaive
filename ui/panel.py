from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field

from ecs.components import Inventory
from items.inventory import get_free_slots, get_used_slots
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
        from ecs.components import Experience, Health, IsPlayer, Mana, Position, Stats

        inner: Rect = self.inner_rect

        player_entities: set[int] = world.get_entities_with(IsPlayer)
        if not player_entities:
            return

        player = next(iter(player_entities))

        y: int = inner.y

        # Header: Name and Level
        exp: Experience = world.component_for(player, Experience)
        level_str = f"Lv.{exp.level}" if exp else ""
        terminal.draw_string_at_layer(inner.x, y, "Player", "white", self.content_layer)
        terminal.draw_string_at_layer(
            inner.x + inner.width - len(level_str),
            y,
            level_str,
            "yellow",
            self.content_layer,
        )
        y += 1

        separator: str = "-" * inner.width
        terminal.draw_string_at_layer(
            inner.x, y, separator, "dark gray", self.content_layer
        )
        y += 1

        # HP
        stats: Stats = world.component_for(player, Stats)
        health: Health = world.component_for(player, Health)
        if health and stats and exp:
            max_hp = health.max_hp(stats, exp.level)
            hp_pct = health.current_hp / max_hp
            hp_color = "green" if hp_pct > 0.5 else "yellow" if hp_pct > 0.25 else "red"
            hp_text = f"HP: {health.current_hp}/{max_hp}"
            terminal.draw_string_at_layer(
                inner.x, y, hp_text, hp_color, self.content_layer
            )
            y += 1

        # MP
        mana: Mana = world.component_for(player, Mana)
        if mana and stats and exp:
            max_mp = mana.max_mp(stats, exp.level)
            mp_text = f"MP: {mana.current_mp}/{max_mp}"
            terminal.draw_string_at_layer(
                inner.x, y, mp_text, "light blue", self.content_layer
            )
            y += 1

        # XP
        if exp:
            current, needed = exp.xp_progress()
            xp_text = f"XP: {current}/{needed}"
            terminal.draw_string_at_layer(
                inner.x, y, xp_text, "gray", self.content_layer
            )
            y += 2

        # Stats (display in two columns)
        if stats:
            col1_x = inner.x
            col2_x = inner.x + inner.width // 2

            terminal.draw_string_at_layer(
                col1_x, y, f"STR: {stats.strength:2}", "white", self.content_layer
            )
            terminal.draw_string_at_layer(
                col2_x, y, f"INT: {stats.intelligence:2}", "white", self.content_layer
            )
            y += 1
            terminal.draw_string_at_layer(
                col1_x, y, f"DEX: {stats.dexterity:2}", "white", self.content_layer
            )
            terminal.draw_string_at_layer(
                col2_x, y, f"WIS: {stats.wisdom:2}", "white", self.content_layer
            )
            y += 1
            terminal.draw_string_at_layer(
                col1_x, y, f"CON: {stats.constitution:2}", "white", self.content_layer
            )
            terminal.draw_string_at_layer(
                col2_x, y, f"CHA: {stats.charisma:2}", "white", self.content_layer
            )
            y += 2

        # Show how much inventory space the player has available
        inventory: Inventory = world.component_for(player, Inventory)
        terminal.draw_string_at_layer(
            inner.x,
            y,
            f"Inventory: {get_used_slots(world, player)}/{inventory.max_slots}",
            "gray",
            self.content_layer,
        )


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
