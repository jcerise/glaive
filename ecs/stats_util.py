from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ecs.components import Experience, Stats


def get_damage_bonus(stats: "Stats") -> int:
    return (stats.strentgh - 10) // 2


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
