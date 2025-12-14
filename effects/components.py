from dataclasses import dataclass, field

from ecs.components import Component
from effects.effect_types import Effect


@dataclass
class ActiveEffects(Component):
    """
    Tracks all active duration-based effects on an entity.

    Effects stack additively - multiple poison effects will each deal their
    damage separately.
    """

    effects: list[Effect] = field(default_factory=list)

    def add_effect(self, effect: Effect) -> None:
        """Add an effect. Effects of the same type stack additively."""
        self.effects.append(effect)

    def tick_effects(self) -> list[Effect]:
        """
        Decrement all effect durations by 1.
        Returns list of effects that expired this tick.
        """
        expired: list[Effect] = []
        remaining: list[Effect] = []

        for effect in self.effects:
            effect.duration -= 1
            if effect.duration <= 0:
                expired.append(effect)
            else:
                remaining.append(effect)

        self.effects = remaining
        return expired

    def get_stat_modifiers(self) -> dict[str, int]:
        """Get total stat modifiers from all active effects."""
        totals: dict[str, int] = {}
        for effect in self.effects:
            for stat, value in effect.stat_modifiers.items():
                totals[stat] = totals.get(stat, 0) + value
        return totals

    def has_effect_type(self, effect_type: str) -> bool:
        """Check if entity has any active effect of the given type."""
        return any(e.effect_type.value == effect_type for e in self.effects)

    def get_effects_by_type(self, effect_type: str) -> list[Effect]:
        """Get all active effects of a given type."""
        return [e for e in self.effects if e.effect_type.value == effect_type]
