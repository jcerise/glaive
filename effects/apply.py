from typing import TYPE_CHECKING

from ecs.components import Health, Mana, Stats, Experience
from effects.components import ActiveEffects
from effects.effect_types import Effect, EffectType

if TYPE_CHECKING:
    from ecs.world import World


def apply_effect_to_entity(world: "World", target: int, effect: Effect) -> str:
    """
    Apply an effect to a target entity.

    For instant effects (duration=0), applies immediately and returns result.
    For duration effects (duration>0), adds to entity's ActiveEffects component.

    Returns a message describing what happened.
    """
    if effect.duration == 0:
        # Instant effect - apply immediately
        return _apply_instant_effect(world, target, effect)
    else:
        # Duration effect - add to ActiveEffects
        active = world.get_component(target, ActiveEffects)
        if not active:
            active = ActiveEffects()
            world.add_component(target, active)
        active.add_effect(effect)
        return f"{effect.name} applied for {effect.duration} turns"


def _apply_instant_effect(world: "World", target: int, effect: Effect) -> str:
    """Apply an instant effect to a target entity."""
    health = world.get_component(target, Health)
    mana = world.get_component(target, Mana)
    stats = world.get_component(target, Stats)
    exp = world.get_component(target, Experience)
    level = exp.level if exp else 1

    if effect.effect_type == EffectType.HEAL:
        if not health:
            return "no effect (target has no health)"
        if not stats:
            max_hp = health.base_max_hp
        else:
            max_hp = health.max_hp(stats, level)

        old_hp = health.current_hp
        health.current_hp = min(health.current_hp + effect.power, max_hp)
        healed = health.current_hp - old_hp

        if healed > 0:
            return f"restored {healed} HP"
        else:
            return "no effect (already at full health)"

    elif effect.effect_type == EffectType.DAMAGE:
        if not health:
            return "no effect (target has no health)"
        health.current_hp -= effect.power
        return f"dealt {effect.power} damage"

    elif effect.effect_type == EffectType.RESTORE_MANA:
        if not mana:
            return "no effect (target has no mana)"
        if not stats:
            max_mp = mana.base_max_mp
        else:
            max_mp = mana.max_mp(stats, level)

        old_mp = mana.current_mp
        mana.current_mp = min(mana.current_mp + effect.power, max_mp)
        restored = mana.current_mp - old_mp

        if restored > 0:
            return f"restored {restored} MP"
        else:
            return "no effect (already at full mana)"

    elif effect.effect_type == EffectType.DRAIN_MANA:
        if not mana:
            return "no effect (target has no mana)"
        old_mp = mana.current_mp
        mana.current_mp = max(mana.current_mp - effect.power, 0)
        drained = old_mp - mana.current_mp
        return f"drained {drained} MP"

    elif effect.effect_type in (EffectType.POISON, EffectType.REGEN):
        # These should typically be duration effects, but handle instant case
        if not health:
            return "no effect (target has no health)"

        if effect.effect_type == EffectType.POISON:
            health.current_hp -= effect.power
            return f"dealt {effect.power} poison damage"
        else:
            if not stats:
                max_hp = health.base_max_hp
            else:
                max_hp = health.max_hp(stats, level)
            old_hp = health.current_hp
            health.current_hp = min(health.current_hp + effect.power, max_hp)
            healed = health.current_hp - old_hp
            return f"regenerated {healed} HP"

    elif effect.effect_type in (EffectType.STAT_BUFF, EffectType.STAT_DEBUFF):
        # Stat modifiers only make sense for duration effects
        if effect.stat_modifiers:
            mods = ", ".join(
                f"{stat} {'+' if val > 0 else ''}{val}"
                for stat, val in effect.stat_modifiers.items()
            )
            return f"modified stats: {mods}"
        return "no effect (no stat modifiers)"

    return "no effect"
