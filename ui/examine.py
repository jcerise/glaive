from typing import TYPE_CHECKING

from ecs.components import Drawable
from items.affixes import ItemAffixes
from items.components import Consumable, Equipment, Item, Treasure
from items.item_types import RARITY_COLORS
from ui.popup import Popup

if TYPE_CHECKING:
    from ecs.world import World
    from terminal.terminal import GlaiveTerminal


def create_examine_popup(world: "World", item_id: int) -> Popup:
    """Create a formatted popup for examining an item in detail"""

    drawable: Drawable = world.component_for(item_id, Drawable)
    item: Item = world.component_for(item_id, Item)
    equipment: Equipment | None = world.get_component(item_id, Equipment)
    consumable: Consumable | None = world.get_component(item_id, Consumable)
    treasure: Treasure | None = world.get_component(item_id, Treasure)
    affixes: ItemAffixes | None = world.get_component(item_id, ItemAffixes)

    # Calculate display name
    if affixes:
        display_name = affixes.get_display_name(drawable.name)
    else:
        display_name = drawable.name

    # Calculate required width based on content
    lines: list[str] = []
    lines.append(display_name)
    lines.append(f"({item.rarity.capitalize()})")

    if equipment:
        if equipment.base_damage > 0:
            lines.append(f"  Damage: +{equipment.base_damage}")
        if equipment.base_defense > 0:
            lines.append(f"  Defense: +{equipment.base_defense}")
        lines.append(f"  Slot: {equipment.slot}")
    elif consumable:
        lines.append(f"  Effect: {consumable.effect_type}")
        lines.append(f"  Power: {consumable.effect_power}")
        lines.append(f"  Uses: {consumable.uses_remaining}")
    elif treasure:
        lines.append(f"  Type: {treasure.treasure_type}")

    if affixes:
        for affix in [affixes.prefix, affixes.suffix]:
            if affix:
                lines.append(f"  {affix.name}:")
                for stat, value in affix.stat_modifiers.items():
                    sign = "+" if value > 0 else ""
                    lines.append(f"    {sign}{value} {stat}")

    lines.append(f"  {item.base_value} gold")

    # Calculate dimensions
    max_content_width = max(len(line) for line in lines)
    # Add padding: 2 for border, 2 for inner padding
    popup_width = max(max_content_width + 4, 20)

    # Calculate height: items + section headers + separators + spacing
    content_lines = 4  # name, rarity, blank, "Base Stats" header
    content_lines += 1  # separator
    if equipment:
        content_lines += 1  # slot
        if equipment.base_damage > 0:
            content_lines += 1
        if equipment.base_defense > 0:
            content_lines += 1
    elif consumable:
        content_lines += 3  # effect, power, uses
    elif treasure:
        content_lines += 1  # type
    content_lines += 1  # blank

    if affixes and (affixes.prefix or affixes.suffix):
        content_lines += 2  # header + separator
        for affix in [affixes.prefix, affixes.suffix]:
            if affix:
                content_lines += 1 + len(affix.stat_modifiers)  # name + stats
        content_lines += 1  # blank

    content_lines += 3  # Value header, separator, value
    popup_height = content_lines + 2  # +2 for border

    def render_examine_content(
        popup: Popup, terminal: "GlaiveTerminal", world: "World", layer: int
    ):
        inner = popup.inner_rect
        if not inner:
            return

        y = inner.y

        color = RARITY_COLORS.get(item.rarity, "white")
        if affixes:
            name = affixes.get_display_name(drawable.name)
        else:
            name = drawable.name
        terminal.draw_string_at_layer(inner.x, y, name, color, layer)
        y += 1
        terminal.draw_string_at_layer(
            inner.x, y, f"({item.rarity.capitalize()})", color, layer
        )
        y += 2

        separator = "-" * inner.width
        terminal.draw_string_at_layer(inner.x, y, "Base Stats", "yellow", layer)
        y += 1
        terminal.draw_string_at_layer(inner.x, y, separator, "dark gray", layer)
        y += 1

        if equipment:
            if equipment.base_damage > 0:
                terminal.draw_string_at_layer(
                    inner.x, y, f"  Damage: +{equipment.base_damage}", "white", layer
                )
                y += 1
            if equipment.base_defense > 0:
                terminal.draw_string_at_layer(
                    inner.x, y, f"  Defense: +{equipment.base_defense}", "white", layer
                )
                y += 1
            terminal.draw_string_at_layer(
                inner.x, y, f"  Slot: {equipment.slot}", "gray", layer
            )
            y += 1
        elif consumable:
            terminal.draw_string_at_layer(
                inner.x, y, f"  Effect: {consumable.effect_type}", "white", layer
            )
            y += 1
            terminal.draw_string_at_layer(
                inner.x, y, f"  Power: {consumable.effect_power}", "white", layer
            )
            y += 1
            terminal.draw_string_at_layer(
                inner.x, y, f"  Uses: {consumable.uses_remaining}", "gray", layer
            )
            y += 1
        elif treasure:
            terminal.draw_string_at_layer(
                inner.x, y, f"  Type: {treasure.treasure_type}", "white", layer
            )
            y += 1

        y += 1

        if affixes and (affixes.prefix or affixes.suffix):
            terminal.draw_string_at_layer(inner.x, y, "Enchantments", "yellow", layer)
            y += 1
            terminal.draw_string_at_layer(inner.x, y, separator, "dark gray", layer)
            y += 1

            for affix in [affixes.prefix, affixes.suffix]:
                if affix:
                    terminal.draw_string_at_layer(
                        inner.x, y, f"  {affix.name}:", "green", layer
                    )
                    y += 1
                    for stat, value in affix.stat_modifiers.items():
                        sign = "+" if value > 0 else ""
                        terminal.draw_string_at_layer(
                            inner.x + 4, y, f"{sign}{value} {stat}", "white", layer
                        )
                        y += 1
            y += 1

        terminal.draw_string_at_layer(inner.x, y, "Value", "yellow", layer)
        y += 1
        terminal.draw_string_at_layer(inner.x, y, separator, "dark gray", layer)
        y += 1
        terminal.draw_string_at_layer(
            inner.x, y, f"  {item.base_value} gold", "white", layer
        )

    return Popup(
        width=popup_width,
        height=popup_height,
        title="Examine",
        content_renderer=render_examine_content,
    )
