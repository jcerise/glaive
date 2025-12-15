from typing import TYPE_CHECKING

from ecs.components import Drawable, Health, IsActor, Position, Stats
from effects.apply import apply_effect_to_entity
from effects.effect_types import EffectType
from effects.pools import create_pool
from effects.targeting import get_chebyshev_distance
from items.components import Consumable, InInventory, Item, OnGround
from items.consumable_actions import create_effect_from_consumable

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
    - If AoE consumable: applies effect to all entities in radius, optionally creates pools
    - If single-target consumable hits an entity: applies effect directly to them
    - If consumable lands on empty tile: creates pool (if liquid) or shatters
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

    # Handle AoE consumables (radius > 0)
    if consumable and consumable.radius > 0:
        return _handle_aoe_consumable(
            world, thrower, item_id, drawable, consumable, target_x, target_y
        )

    # Handle single-target consumables (radius = 0)
    if consumable:
        return _handle_single_target_consumable(
            world, thrower, item_id, drawable, item, consumable, target_x, target_y
        )

    # Non-consumable items just land at the target location
    world.add_component(item_id, Position(x=target_x, y=target_y))
    world.add_component(item_id, OnGround())
    return True, f"Threw {drawable.name}."


def _handle_aoe_consumable(
    world: "World",
    thrower: int,
    item_id: int,
    drawable: Drawable,
    consumable: Consumable,
    target_x: int,
    target_y: int,
) -> tuple[bool, str]:
    """Handle throwing an AoE consumable (radius > 0)."""
    effect = create_effect_from_consumable(consumable, drawable.name)
    effect_type = _get_effect_type(consumable.effect_type)
    item_color = drawable.glyph.fg_color
    radius = consumable.radius
    pool_name = consumable.pool_name

    # Find all entities in radius and apply effect
    entities_hit = _get_entities_in_radius(world, target_x, target_y, radius)
    hit_count = 0

    for entity in entities_hit:
        apply_effect_to_entity(world, entity, effect)
        hit_count += 1

    # Create pools at all tiles in radius if creates_pool is True
    if consumable.creates_pool and effect_type:
        tiles = _get_tiles_in_radius(target_x, target_y, radius)
        for tx, ty in tiles:
            create_pool(
                world,
                tx,
                ty,
                effect_type,
                consumable.effect_power,
                source_entity=thrower,
                color=item_color,
                name=pool_name,
            )

    _destroy_item(world, item_id)

    # Build result message
    if hit_count > 0:
        return True, f"{drawable.name} explodes! Hit {hit_count} target(s)."
    elif consumable.creates_pool:
        return True, f"{drawable.name} explodes, creating pools!"
    else:
        return True, f"{drawable.name} explodes!"


def _handle_single_target_consumable(
    world: "World",
    thrower: int,
    item_id: int,
    drawable: Drawable,
    item: Item | None,
    consumable: Consumable,
    target_x: int,
    target_y: int,
) -> tuple[bool, str]:
    """Handle throwing a single-target consumable (radius = 0)."""
    # Check if there's an entity at the target tile
    target_entity = _get_entity_at(world, target_x, target_y)

    if target_entity is not None:
        # Consumable hits an entity - apply effect directly
        target_drawable = world.get_component(target_entity, Drawable)
        target_name = target_drawable.name if target_drawable else "something"

        effect = create_effect_from_consumable(consumable, drawable.name)
        result_msg = apply_effect_to_entity(world, target_entity, effect)

        _destroy_item(world, item_id)
        return True, f"Threw {drawable.name} at {target_name}: {result_msg}"

    elif consumable.creates_pool:
        # Liquid consumable lands on empty tile - creates a ground pool
        effect_type = _get_effect_type(consumable.effect_type)
        if effect_type:
            item_color = drawable.glyph.fg_color
            pool_name = consumable.pool_name
            create_pool(
                world,
                target_x,
                target_y,
                effect_type,
                consumable.effect_power,
                source_entity=thrower,
                color=item_color,
                name=pool_name,
            )
        _destroy_item(world, item_id)
        return True, f"Threw {drawable.name} - it shatters on impact!"

    elif _is_breakable(item):
        # Non-liquid breakable consumable - just shatters
        _destroy_item(world, item_id)
        return True, f"Threw {drawable.name} - it shatters on impact!"

    else:
        # Shouldn't happen for consumables, but fallback
        _destroy_item(world, item_id)
        return True, f"Threw {drawable.name}."


def _get_entity_at(world: "World", x: int, y: int) -> int | None:
    """
    Find an actor entity at the specified tile.

    Returns the entity ID or None if no actor is present.
    Only returns entities with IsActor and Health (targetable entities).
    """
    for entity in world.get_entities_with(IsActor, Position, Health):
        pos = world.component_for(entity, Position)
        if pos.x == x and pos.y == y:
            return entity
    return None


def _get_entities_in_radius(
    world: "World", center_x: int, center_y: int, radius: int
) -> list[int]:
    """
    Find all actor entities within radius of the center tile.

    Uses Chebyshev distance (king's move). Includes center tile.
    """
    entities = []
    for entity in world.get_entities_with(IsActor, Position, Health):
        pos = world.component_for(entity, Position)
        distance = get_chebyshev_distance(center_x, center_y, pos.x, pos.y)
        if distance <= radius:
            entities.append(entity)
    return entities


def _get_tiles_in_radius(
    center_x: int, center_y: int, radius: int
) -> list[tuple[int, int]]:
    """
    Get all tile coordinates within radius of the center.

    Uses Chebyshev distance (king's move). Includes center tile.
    """
    tiles = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if get_chebyshev_distance(0, 0, dx, dy) <= radius:
                tiles.append((center_x + dx, center_y + dy))
    return tiles


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
