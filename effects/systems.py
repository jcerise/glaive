from typing import TYPE_CHECKING

from ecs.components import Drawable, Health, IsPlayer, Stats, Experience
from ecs.resources import UIResource
from ecs.systems import System
from ecs.world import World
from effects.components import ActiveEffects
from effects.effect_types import Effect, EffectType

if TYPE_CHECKING:
    from ui.state import UIState


class EffectTickSystem(System):
    """
    Process duration-based effects each turn.

    Runs in the resolution phase. For each entity with ActiveEffects:
    1. Apply tick damage/healing for each effect
    2. Decrement effect durations
    3. Remove expired effects
    4. Remove ActiveEffects component if no effects remain
    """

    def update(self, world: World) -> None:
        entities_to_clean: list[int] = []

        for entity in world.get_entities_with(ActiveEffects):
            active = world.component_for(entity, ActiveEffects)
            health = world.get_component(entity, Health)
            stats = world.get_component(entity, Stats)
            exp = world.get_component(entity, Experience)
            level = exp.level if exp else 1

            # Apply tick effects
            for effect in active.effects:
                self._apply_tick(world, entity, effect, health, stats, level)

            # Tick durations and get expired effects
            expired = active.tick_effects()

            # Log expired effects for player
            for effect in expired:
                self._log_expiration(world, entity, effect)

            # Mark for cleanup if no effects remain
            if not active.effects:
                entities_to_clean.append(entity)

        # Remove empty ActiveEffects components
        for entity in entities_to_clean:
            world.remove_component(entity, ActiveEffects)

    def _apply_tick(
        self,
        world: World,
        entity: int,
        effect: Effect,
        health: Health | None,
        stats: Stats | None,
        level: int,
    ) -> None:
        """Apply the per-tick effect of a duration effect."""
        if effect.effect_type == EffectType.POISON and health:
            damage = effect.power
            health.current_hp -= damage
            self._log_tick(world, entity, f"take {damage} poison damage")

        elif effect.effect_type == EffectType.REGEN and health and stats:
            heal = effect.power
            max_hp = health.max_hp(stats, level)
            old_hp = health.current_hp
            health.current_hp = min(health.current_hp + heal, max_hp)
            actual_heal = health.current_hp - old_hp
            if actual_heal > 0:
                self._log_tick(world, entity, f"regenerate {actual_heal} HP")

        elif effect.effect_type == EffectType.DAMAGE and health:
            damage = effect.power
            health.current_hp -= damage
            self._log_tick(world, entity, f"take {damage} damage")

    def _log_tick(self, world: World, entity: int, message: str) -> None:
        """Log a tick effect message for the player."""
        is_player = world.get_component(entity, IsPlayer)
        if is_player:
            ui_state: "UIState" = world.resource_for(UIResource)
            ui_state.message_log.add(f"You {message}.", "light blue")
        else:
            # For non-player entities, we could log to player if visible
            drawable = world.get_component(entity, Drawable)
            if drawable:
                ui_state: "UIState" = world.resource_for(UIResource)
                ui_state.message_log.add(
                    f"{drawable.name} {message}s.", "light gray"
                )

    def _log_expiration(self, world: World, entity: int, effect: Effect) -> None:
        """Log when an effect expires."""
        is_player = world.get_component(entity, IsPlayer)
        if is_player:
            ui_state: "UIState" = world.resource_for(UIResource)
            ui_state.message_log.add(f"{effect.name} wears off.", "gray")
