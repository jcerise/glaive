"""Actions for throwing items."""

from typing import TYPE_CHECKING

from ecs.components import Drawable, Position, Stats
from effects.effect_types import EffectType
from effects.pools import create_pool
from items.components import Consumable, InInventory, Item, OnGround

if TYPE_CHECKING:
    from ecs.world import World


def get_throw_range(world: "World", thrower: int) -> int:
    """
    Calculate throw range based on Strength stat.

    Base range is 5, plus (strength - 10) // 2.
    Minimum range is 2.
    """
    BASE_RANGE = 5
    MIN_RANGE = 2

    stats = world.get_component(thrower, Stats)
    if stats:
        strength_bonus = (stats.strength - 10) // 2
        return max(MIN_RANGE, BASE_RANGE + strength_bonus)

    return BASE_RANGE


def throw_item(
    world: "World", thrower: int, item_id: int, target_x: int, target_y: int
) -> tuple[bool, str]:
    """
    Throw an item to a target location.

    Returns (success, message) tuple.

    Behavior:
    - Removes item from thrower's inventory
    - For potions: will break and create ground pool (Phase 5)
    - For other items: drops at target location
    """
    # Verify item is in thrower's inventory
    in_inv = world.get_component(item_id, InInventory)
    if not in_inv or in_inv.owner != thrower:
        return False, "Item not in inventory"

    drawable = world.component_for(item_id, Drawable)
    item = world.get_component(item_id, Item)
    consumable = world.get_component(item_id, Consumable)

    # Remove from inventory
    world.remove_component(item_id, InInventory)

    # Determine behavior based on item type
    if consumable and consumable.creates_pool:
        # Liquid consumable (potion/vial) - creates a ground pool
        effect_type = _get_effect_type(consumable.effect_type)
        if effect_type:
            # Use the item's glyph color for the pool
            item_color = drawable.glyph.fg_color
            create_pool(
                world,
                target_x,
                target_y,
                effect_type,
                consumable.effect_power,
                source_entity=thrower,
                color=item_color,
            )
        _destroy_item(world, item_id)
        return True, f"Threw {drawable.name} - it shatters on impact!"
    elif consumable and _is_breakable(item):
        # Non-liquid breakable consumable - just shatters
        _destroy_item(world, item_id)
        return True, f"Threw {drawable.name} - it shatters on impact!"
    else:
        # Other items just land at the target location
        world.add_component(item_id, Position(x=target_x, y=target_y))
        world.add_component(item_id, OnGround())
        return True, f"Threw {drawable.name}."


def _get_effect_type(effect_type_str: str) -> EffectType | None:
    """Convert effect type string to EffectType enum."""
    try:
        return EffectType(effect_type_str)
    except ValueError:
        return None


def _is_breakable(item: Item | None) -> bool:
    """
    Check if an item breaks when thrown.

    Currently, all consumables are considered breakable (potions).
    This can be extended later with a component or item property.
    """
    if not item:
        return False
    # For now, consumables break on throw
    # Later we can add a "breaks_on_throw" field to Consumable
    return item.item_type == "consumable"


def _destroy_item(world: "World", item_id: int) -> None:
    """Remove all components from an item entity, effectively destroying it."""
    for comp_type in list(world._components.keys()):
        if item_id in world._components.get(comp_type, {}):
            world.remove_component(item_id, comp_type)
