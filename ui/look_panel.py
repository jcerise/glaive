"""Look mode info panel - displays information about what's at the cursor position."""
from typing import TYPE_CHECKING

from ecs.components import Drawable, IsActor, Position
from ecs.resources import MapResource
from items.components import Item, OnGround
from map.map import TILE_PROPERTIES
from ui.popup import Popup

if TYPE_CHECKING:
    from ecs.world import World
    from terminal.terminal import GlaiveTerminal


def create_look_info_panel(world: "World", cursor_x: int, cursor_y: int) -> Popup:
    """Create an info panel showing what's at the cursor position."""

    # Gather information about the position
    game_map = world.resource_for(MapResource)

    # Get tile info
    tile_type = game_map.get_tile(cursor_x, cursor_y)
    tile_props = TILE_PROPERTIES[tile_type]
    tile_name = tile_type.name.replace("_", " ").title()

    # Check visibility
    is_visible = game_map.is_visible(cursor_x, cursor_y)
    is_explored = game_map.is_explored(cursor_x, cursor_y)

    # Get entities at position
    entity_names: list[str] = []

    if is_visible or is_explored:
        # Get items on ground
        for entity_id in world.get_entities_with(OnGround, Position, Item, Drawable):
            pos = world.component_for(entity_id, Position)
            if pos.x == cursor_x and pos.y == cursor_y:
                drawable = world.component_for(entity_id, Drawable)
                entity_names.append(drawable.name)

        # Get actors
        for entity_id in world.get_entities_with(IsActor, Position, Drawable):
            pos = world.component_for(entity_id, Position)
            if pos.x == cursor_x and pos.y == cursor_y:
                drawable = world.component_for(entity_id, Drawable)
                entity_names.append(drawable.name)

    # Build display lines
    lines: list[tuple[str, str]] = []  # (text, color)

    lines.append((f"({cursor_x}, {cursor_y})", "dark gray"))

    if not is_explored:
        lines.append(("Unexplored", "dark gray"))
    else:
        # Tile info
        lines.append((tile_name, "white"))

        # Entity list
        if entity_names:
            lines.append(("", "white"))  # Blank line
            for name in entity_names:
                lines.append((f"  {name}", "yellow"))

        if not is_visible:
            lines.append(("", "white"))
            lines.append(("(remembered)", "dark gray"))

    # Calculate popup dimensions
    max_width = max(len(line[0]) for line in lines) if lines else 10
    popup_width = max(max_width + 4, 16)  # +4 for border and padding
    popup_height = len(lines) + 2  # +2 for border

    def render_content(
        popup: Popup, terminal: "GlaiveTerminal", world: "World", layer: int
    ):
        inner = popup.inner_rect
        if not inner:
            return

        y = inner.y
        for text, color in lines:
            if text:
                terminal.draw_string_at_layer(inner.x, y, text, color, layer)
            y += 1

    return Popup(
        width=popup_width,
        height=popup_height,
        title="Look",
        content_renderer=render_content,
    )
