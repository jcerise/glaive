"""Helper functions for creating and managing ground pools."""

from typing import TYPE_CHECKING

from ecs.components import Drawable, Position
from effects.components import GroundPool
from effects.effect_types import EffectType
from terminal.glyph import Glyph

if TYPE_CHECKING:
    from ecs.world import World

# Pool duration in turns
POOL_DURATION = 5

# Colors for different pool effect types
POOL_COLORS: dict[EffectType, str] = {
    EffectType.HEAL: "light green",
    EffectType.DAMAGE: "red",
    EffectType.POISON: "purple",
    EffectType.REGEN: "green",
    EffectType.RESTORE_MANA: "light blue",
    EffectType.DRAIN_MANA: "dark blue",
    EffectType.STAT_BUFF: "yellow",
    EffectType.STAT_DEBUFF: "orange",
}

# Names for pool messages
POOL_NAMES: dict[EffectType, str] = {
    EffectType.HEAL: "healing liquid",
    EffectType.DAMAGE: "harmful liquid",
    EffectType.POISON: "poisonous liquid",
    EffectType.REGEN: "regenerative liquid",
    EffectType.RESTORE_MANA: "mana-restoring liquid",
    EffectType.DRAIN_MANA: "mana-draining liquid",
    EffectType.STAT_BUFF: "empowering liquid",
    EffectType.STAT_DEBUFF: "weakening liquid",
}


def get_pool_at(world: "World", x: int, y: int) -> int | None:
    """
    Get the pool entity at a specific tile, if one exists.

    Returns the entity ID or None.
    """
    for entity in world.get_entities_with(GroundPool, Position):
        pos = world.component_for(entity, Position)
        if pos.x == x and pos.y == y:
            return entity
    return None


def remove_pool_at(world: "World", x: int, y: int) -> bool:
    """
    Remove any existing pool at the specified tile.

    Returns True if a pool was removed.
    """
    pool_entity = get_pool_at(world, x, y)
    if pool_entity is not None:
        _destroy_pool(world, pool_entity)
        return True
    return False


def create_pool(
    world: "World",
    x: int,
    y: int,
    effect_type: EffectType,
    power: int,
    source_entity: int | None = None,
    duration: int = POOL_DURATION,
    color: str | None = None,
) -> int:
    """
    Create a ground pool at the specified location.

    If a pool already exists at that tile, it is replaced.

    Args:
        world: The game world
        x, y: Tile coordinates
        effect_type: Type of effect the pool applies
        power: Power of the effect
        source_entity: Who created this pool (for attribution)
        duration: How many turns the pool lasts
        color: Pool color (if None, uses default color for effect type)

    Returns:
        The entity ID of the created pool
    """
    # Remove any existing pool at this location (one pool per tile)
    remove_pool_at(world, x, y)

    # Get visual properties - use provided color or fall back to effect type default
    if color is None:
        color = POOL_COLORS.get(effect_type, "white")
    pool_name = POOL_NAMES.get(effect_type, "strange liquid")

    # Create pool entity
    entity = world.create_entity()
    world.add_component(entity, Position(x=x, y=y))
    world.add_component(entity, Drawable(Glyph("~", color), f"pool of {pool_name}"))
    world.add_component(
        entity,
        GroundPool(
            effect_type=effect_type,
            power=power,
            duration=duration,
            name=pool_name,
            source_entity=source_entity,
        ),
    )

    return entity


def _destroy_pool(world: "World", pool_entity: int) -> None:
    """Remove all components from a pool entity, destroying it."""
    for comp_type in list(world._components.keys()):
        if pool_entity in world._components.get(comp_type, {}):
            world.remove_component(pool_entity, comp_type)
