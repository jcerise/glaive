from typing import TYPE_CHECKING

from ecs.components import Drawable
from effects.apply import apply_effect_to_entity
from effects.effect_types import Effect, EffectType
from items.components import Consumable, InInventory

if TYPE_CHECKING:
    from ecs.world import World


def consume_item(world: "World", user: int, item_id: int) -> tuple[bool, str]:
    """
    Consume an item, applying its effect to the user.

    Returns (success, message) tuple.
    """
    consumable = world.get_component(item_id, Consumable)
    if not consumable:
        return False, "Item is not consumable"

    in_inv = world.get_component(item_id, InInventory)
    if not in_inv or in_inv.owner != user:
        return False, "Item not in inventory"

    drawable = world.component_for(item_id, Drawable)

    # Create effect from consumable data
    effect = create_effect_from_consumable(consumable, drawable.name)

    # Apply effect to user
    result_msg = apply_effect_to_entity(world, user, effect)

    # Decrement uses
    consumable.uses_remaining -= 1

    # Destroy item if no uses left
    if consumable.uses_remaining <= 0:
        destroy_item(world, item_id)
        return True, f"Used {drawable.name}: {result_msg}"
    else:
        return True, f"Used {drawable.name}: {result_msg} ({consumable.uses_remaining} uses left)"


def create_effect_from_consumable(consumable: Consumable, item_name: str) -> Effect:
    """Convert a Consumable component's data into an Effect."""
    # Map consumable effect_type string to EffectType enum
    effect_type_map = {
        "heal": EffectType.HEAL,
        "damage": EffectType.DAMAGE,
        "poison": EffectType.POISON,
        "regen": EffectType.REGEN,
        "restore_mana": EffectType.RESTORE_MANA,
        "drain_mana": EffectType.DRAIN_MANA,
        "stat_buff": EffectType.STAT_BUFF,
        "stat_debuff": EffectType.STAT_DEBUFF,
    }

    effect_type = effect_type_map.get(consumable.effect_type, EffectType.HEAL)

    return Effect(
        name=item_name,
        effect_type=effect_type,
        power=consumable.effect_power,
        duration=consumable.effect_duration,
        stat_modifiers=dict(consumable.stat_modifiers),  # Copy the dict
    )


def destroy_item(world: "World", item_id: int) -> None:
    """Remove all components from an item entity, effectively destroying it."""
    # Get all component types and remove this entity from each
    for comp_type in list(world._components.keys()):
        if item_id in world._components.get(comp_type, {}):
            world.remove_component(item_id, comp_type)
