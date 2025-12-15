import random
from typing import TYPE_CHECKING

from ecs.components import Drawable, Position
from items.affixes import apply_affixes_for_rarity
from items.components import Consumable, Equipment, Item, OnGround, Treasure
from terminal.terminal import Glyph

if TYPE_CHECKING:
    from ecs.world import World


def roll_rarity() -> str:
    """Roll a random rarity based on standard drop rates."""
    roll = random.random()
    if roll < 0.60:
        return "common"
    elif roll < 0.85:
        return "uncommon"
    elif roll < 0.97:
        return "rare"
    elif roll < 0.995:
        return "epic"
    else:
        return "legendary"


def create_weapon(
    world: "World",
    name: str,
    glyph_char: str,
    glyph_color: str,
    slot: str,
    base_damage: int,
    base_value: int,
    x: int,
    y: int,
    rarity: str | None = None,
) -> int:
    """
    Create a weapon entity with optional random affixes.
    """
    if rarity is None:
        rarity = roll_rarity()

    entity = world.create_entity()
    world.add_component(
        entity, Item(item_type="equipment", base_value=base_value, rarity=rarity)
    )
    world.add_component(entity, Equipment(slot=slot, base_damage=base_damage))
    world.add_component(entity, Drawable(Glyph(glyph_char, glyph_color), name))
    world.add_component(entity, Position(x, y))
    world.add_component(entity, OnGround())

    apply_affixes_for_rarity(world, entity, rarity, slot)

    return entity


def create_armor(
    world: "World",
    name: str,
    glyph_char: str,
    glyph_color: str,
    slot: str,
    base_defense: int,
    base_value: int,
    x: int,
    y: int,
    rarity: str | None = None,
) -> int:
    """
    Create an armor entity with optional random affixes.
    """
    if rarity is None:
        rarity = roll_rarity()

    entity = world.create_entity()
    world.add_component(
        entity, Item(item_type="equipment", base_value=base_value, rarity=rarity)
    )
    world.add_component(entity, Equipment(slot=slot, base_defense=base_defense))
    world.add_component(entity, Drawable(Glyph(glyph_char, glyph_color), name))
    world.add_component(entity, Position(x, y))
    world.add_component(entity, OnGround())

    apply_affixes_for_rarity(world, entity, rarity, slot)

    return entity


def create_consumable(
    world: "World",
    name: str,
    glyph_char: str,
    glyph_color: str,
    effect_type: str,
    effect_power: int,
    base_value: int,
    x: int,
    y: int,
    uses: int = 1,
    creates_pool: bool = False,
    radius: int = 0,
    pool_name: str | None = None,
    effect_duration: int = 0,
    stat_modifiers: dict[str, int] | None = None,
) -> int:
    """
    Create a consumable item entity.

    Args:
        creates_pool: If True, this consumable creates a ground pool when thrown
                     (e.g., potions and vials)
        radius: AoE radius (0 = single target, >0 = affects tiles/entities in radius)
        pool_name: Custom name for created pools (e.g., "water"), uses default if None
        effect_duration: Duration in turns (0 = instant, >0 = lasts N turns)
        stat_modifiers: Dict of stat modifiers (e.g., {"strength": 3})
    """
    entity = world.create_entity()
    world.add_component(entity, Item(item_type="consumable", base_value=base_value))
    world.add_component(
        entity,
        Consumable(
            effect_type=effect_type,
            effect_power=effect_power,
            uses_remaining=uses,
            creates_pool=creates_pool,
            radius=radius,
            pool_name=pool_name,
            effect_duration=effect_duration,
            stat_modifiers=stat_modifiers or {},
        ),
    )
    world.add_component(entity, Drawable(Glyph(glyph_char, glyph_color), name))
    world.add_component(entity, Position(x, y))
    world.add_component(entity, OnGround())

    return entity


def create_consumable_from_template(
    world: "World",
    template_id: str,
    x: int,
    y: int,
) -> int | None:
    """
    Create a consumable item from a template definition.

    Args:
        template_id: The template ID from consumable_defs.py
        x, y: Position to spawn the item

    Returns:
        Entity ID of the created item, or None if template not found
    """
    from items.consumable_defs import get_template

    template = get_template(template_id)
    if template is None:
        return None

    return create_consumable(
        world=world,
        name=template.name,
        glyph_char=template.glyph,
        glyph_color=template.color,
        effect_type=template.effect_type,
        effect_power=template.power,
        base_value=template.base_value,
        x=x,
        y=y,
        uses=1,
        creates_pool=template.creates_pool,
        radius=template.radius,
        pool_name=template.pool_name,
        effect_duration=template.duration,
        stat_modifiers=dict(template.stat_modifiers),
    )


def create_potion(
    world: "World",
    name: str,
    glyph_color: str,
    effect_type: str,
    effect_power: int,
    base_value: int,
    x: int,
    y: int,
) -> int:
    """
    Create a potion item entity.

    Potions are liquid consumables that create ground pools when thrown.
    Uses '!' glyph by convention.
    """
    return create_consumable(
        world=world,
        name=name,
        glyph_char="!",
        glyph_color=glyph_color,
        effect_type=effect_type,
        effect_power=effect_power,
        base_value=base_value,
        x=x,
        y=y,
        uses=1,
        creates_pool=True,
    )


def create_scroll(
    world: "World",
    name: str,
    glyph_color: str,
    effect_type: str,
    effect_power: int,
    base_value: int,
    x: int,
    y: int,
    radius: int = 0,
    creates_pool: bool = False,
    pool_name: str | None = None,
) -> int:
    """
    Create a scroll item entity.

    Scrolls are single-use consumables that can have AoE effects.
    Uses '?' glyph by convention.

    Args:
        radius: AoE radius (0 = single target, >0 = affects area)
        creates_pool: If True, creates pools in the affected area (e.g., Scroll of Flood)
        pool_name: Custom name for created pools (e.g., "water")
    """
    return create_consumable(
        world=world,
        name=name,
        glyph_char="?",
        glyph_color=glyph_color,
        effect_type=effect_type,
        effect_power=effect_power,
        base_value=base_value,
        x=x,
        y=y,
        uses=1,
        creates_pool=creates_pool,
        radius=radius,
        pool_name=pool_name,
    )


def create_treasure(
    world: "World",
    name: str,
    glyph_char: str,
    glyph_color: str,
    treasure_type: str,
    base_value: int,
    x: int,
    y: int,
) -> int:
    """
    Create a treasure item entity.
    """
    entity = world.create_entity()
    world.add_component(entity, Item(item_type="treasure", base_value=base_value))
    world.add_component(entity, Treasure(treasure_type=treasure_type))
    world.add_component(entity, Drawable(Glyph(glyph_char, glyph_color), name))
    world.add_component(entity, Position(x, y))
    world.add_component(entity, OnGround())

    return entity
