from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ecs.components import Experience, Stats
    from ecs.world import World


def get_effective_stats(world: "World", entity: int) -> dict[str, int]:
    """
    Get effective stat values for an entity, including modifiers from active effects.

    Returns a dict with all six stats (strength, dexterity, constitution,
    intelligence, wisdom, charisma) with effect modifiers applied.
    """
    from ecs.components import Stats
    from effects.components import ActiveEffects

    stats = world.get_component(entity, Stats)
    if not stats:
        return {
            "strength": 10,
            "dexterity": 10,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10,
        }

    # Start with base stats
    effective = {
        "strength": stats.strength,
        "dexterity": stats.dexterity,
        "constitution": stats.constitution,
        "intelligence": stats.intelligence,
        "wisdom": stats.wisdom,
        "charisma": stats.charisma,
    }

    # Apply modifiers from active effects
    active_effects = world.get_component(entity, ActiveEffects)
    if active_effects:
        modifiers = active_effects.get_stat_modifiers()
        for stat, modifier in modifiers.items():
            if stat in effective:
                effective[stat] += modifier

    return effective


def get_effective_stat(world: "World", entity: int, stat_name: str) -> int:
    """Get a single effective stat value for an entity."""
    return get_effective_stats(world, entity).get(stat_name, 10)


def get_damage_bonus(stats: "Stats") -> int:
    return (stats.strength - 10) // 2


def get_accuracy_bonus(stats: "Stats") -> int:
    return (stats.dexterity - 10) // 2


def get_dodge_chance(stats: "Stats") -> int:
    return max(0, (stats.dexterity - 10))


def get_magic_power(stats: "Stats") -> int:
    return (stats.intelligence - 10) // 2


def get_magic_resist(stats: "Stats") -> int:
    return max(0, (stats.wisdom - 10))


def check_level_up(exp: "Experience") -> bool:
    return exp.current_xp >= exp.xp_for_next_level()


def apply_level_up(exp: "Experience", stats: "Stats") -> list[str]:
    """
    Apply a level up, not sure whats going to happen here yet
    Stat increases, probably, maybe some skill points?
    """
    exp.level += 1
    return [f"You have gained a level! You are now level {exp.level}"]
