from typing import TYPE_CHECKING

from ecs.components import Drawable, Health, IsActor, IsPlayer, Mana, Position, Stats, Experience, TurnConsumed
from ecs.resources import UIResource
from ecs.systems import System
from ecs.world import World
from effects.components import ActiveEffects, GroundPool
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
        # Only tick effects when a turn is consumed
        turn_consumed = bool(world.get_entities_with(TurnConsumed))
        if not turn_consumed:
            return

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


class GroundPoolSystem(System):
    """
    Process ground pools each turn.

    Runs in the resolution phase. For each pool:
    1. Find entities standing on the pool
    2. Apply the pool's effect to them
    3. Decrement pool duration
    4. Remove expired pools
    """

    def update(self, world: World) -> None:
        from effects.pools import _destroy_pool

        # Only process pools when a turn is consumed
        # Check if any entity has TurnConsumed (indicates a turn passed)
        turn_consumed = bool(world.get_entities_with(TurnConsumed))
        if not turn_consumed:
            return

        pools_to_remove: list[int] = []

        for pool_entity in world.get_entities_with(GroundPool, Position):
            pool = world.component_for(pool_entity, GroundPool)
            pool_pos = world.component_for(pool_entity, Position)

            # Find all actors standing on this pool
            for entity in world.get_entities_with(IsActor, Position, Health):
                entity_pos = world.component_for(entity, Position)
                if entity_pos.x == pool_pos.x and entity_pos.y == pool_pos.y:
                    self._apply_pool_effect(world, entity, pool)

            # Tick down duration
            pool.duration -= 1
            if pool.duration <= 0:
                pools_to_remove.append(pool_entity)

        # Remove expired pools
        for pool_entity in pools_to_remove:
            self._log_pool_dissipate(world, pool_entity)
            _destroy_pool(world, pool_entity)

    def _apply_pool_effect(
        self, world: World, entity: int, pool: GroundPool
    ) -> None:
        """Apply a pool's effect to an entity standing on it."""
        health = world.component_for(entity, Health)
        mana = world.get_component(entity, Mana)
        stats = world.get_component(entity, Stats)
        exp = world.get_component(entity, Experience)
        level = exp.level if exp else 1

        # Log stepping in pool (only once when first applied each turn)
        self._log_pool_step(world, entity, pool)

        # Apply effect based on type
        if pool.effect_type == EffectType.HEAL and stats:
            max_hp = health.max_hp(stats, level)
            old_hp = health.current_hp
            health.current_hp = min(health.current_hp + pool.power, max_hp)
            actual_heal = health.current_hp - old_hp
            if actual_heal > 0:
                self._log_effect(world, entity, f"heal {actual_heal} HP")

        elif pool.effect_type == EffectType.DAMAGE:
            health.current_hp -= pool.power
            self._log_effect(world, entity, f"take {pool.power} damage")

        elif pool.effect_type == EffectType.POISON:
            health.current_hp -= pool.power
            self._log_effect(world, entity, f"take {pool.power} poison damage")

        elif pool.effect_type == EffectType.REGEN and stats:
            max_hp = health.max_hp(stats, level)
            old_hp = health.current_hp
            health.current_hp = min(health.current_hp + pool.power, max_hp)
            actual_heal = health.current_hp - old_hp
            if actual_heal > 0:
                self._log_effect(world, entity, f"regenerate {actual_heal} HP")

        elif pool.effect_type == EffectType.RESTORE_MANA and mana and stats:
            max_mp = mana.max_mp(stats, level)
            old_mp = mana.current_mp
            mana.current_mp = min(mana.current_mp + pool.power, max_mp)
            actual_restore = mana.current_mp - old_mp
            if actual_restore > 0:
                self._log_effect(world, entity, f"restore {actual_restore} MP")

        elif pool.effect_type == EffectType.DRAIN_MANA and mana:
            old_mp = mana.current_mp
            mana.current_mp = max(0, mana.current_mp - pool.power)
            actual_drain = old_mp - mana.current_mp
            if actual_drain > 0:
                self._log_effect(world, entity, f"lose {actual_drain} MP")

    def _log_pool_step(self, world: World, entity: int, pool: GroundPool) -> None:
        """Log when an entity steps in a pool."""
        is_player = world.get_component(entity, IsPlayer)
        if is_player:
            ui_state: "UIState" = world.resource_for(UIResource)
            ui_state.message_log.add(
                f"You stand in a pool of {pool.name}.", "light blue"
            )

    def _log_effect(self, world: World, entity: int, message: str) -> None:
        """Log a pool effect message."""
        is_player = world.get_component(entity, IsPlayer)
        if is_player:
            ui_state: "UIState" = world.resource_for(UIResource)
            ui_state.message_log.add(f"You {message}.", "light blue")
        else:
            drawable = world.get_component(entity, Drawable)
            if drawable:
                ui_state: "UIState" = world.resource_for(UIResource)
                ui_state.message_log.add(f"{drawable.name} {message}s.", "light gray")

    def _log_pool_dissipate(self, world: World, pool_entity: int) -> None:
        """Log when a pool dissipates."""
        pool = world.get_component(pool_entity, GroundPool)
        pool_pos = world.get_component(pool_entity, Position)
        if pool and pool_pos:
            # Check if player can see this tile (for now, always log)
            ui_state: "UIState" = world.resource_for(UIResource)
            ui_state.message_log.add(
                f"The pool of {pool.name} dissipates.", "gray"
            )
