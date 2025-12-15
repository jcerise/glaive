from dataclasses import dataclass, field
from enum import Enum


class EffectType(Enum):
    """Types of effects that can be applied to entities."""

    HEAL = "heal"
    DAMAGE = "damage"
    POISON = "poison"
    REGEN = "regen"
    RESTORE_MANA = "restore_mana"
    DRAIN_MANA = "drain_mana"
    STAT_BUFF = "stat_buff"
    STAT_DEBUFF = "stat_debuff"


@dataclass
class Effect:
    """
    A single effect instance that can be applied to entities.

    Effects can be instant (duration=0) or duration-based (duration>0).
    Duration effects tick each turn, applying their power and then decrementing.
    """

    name: str
    effect_type: EffectType
    power: int = 0  # Instant amount OR per-tick amount for duration effects
    stat_modifiers: dict[str, int] = field(default_factory=dict)
    duration: int = 0  # 0 = instant, >0 = turns remaining
    radius: int = 0  # 0 = single target, >0 = AoE radius
    source_entity: int | None = None  # Who/what caused this effect
