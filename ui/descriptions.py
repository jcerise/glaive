"""Generate narrative descriptions for actors based on their state."""
from typing import TYPE_CHECKING

from ecs.components import Description, Drawable, Experience, Health, Mana, Stats

if TYPE_CHECKING:
    from ecs.world import World


def generate_actor_description(world: "World", entity_id: int) -> str:
    """Generate a full narrative description for an actor entity."""

    # Get base description or fall back to name
    description = world.get_component(entity_id, Description)
    drawable = world.component_for(entity_id, Drawable)

    if description:
        sentences = [description.text]
    else:
        sentences = [f"A {drawable.name}."]

    # Get components for state descriptions
    health = world.get_component(entity_id, Health)
    mana = world.get_component(entity_id, Mana)
    stats = world.get_component(entity_id, Stats)
    experience = world.get_component(entity_id, Experience)

    # Add stat observations first (physical appearance)
    if stats:
        stat_desc = _describe_stats(stats)
        if stat_desc:
            sentences.append(stat_desc)

    # Add mana description (magical aura)
    if mana and stats:
        level = experience.level if experience else 1
        max_mp = mana.max_mp(stats, level)
        mana_desc = _describe_mana(mana.current_mp, max_mp)
        if mana_desc:
            sentences.append(mana_desc)

    # Add health description last (current condition)
    if health and stats:
        level = experience.level if experience else 1
        max_hp = health.max_hp(stats, level)
        health_desc = _describe_health(health.current_hp, max_hp)
        if health_desc:
            sentences.append(health_desc)

    return " ".join(sentences)


def _describe_health(current_hp: int, max_hp: int) -> str | None:
    """Generate a health state description."""
    if max_hp <= 0:
        return None

    percent = (current_hp / max_hp) * 100

    if percent >= 100:
        return "It appears to be in perfect health."
    elif percent >= 75:
        return "It has a few minor wounds."
    elif percent >= 50:
        return "It appears to be wounded."
    elif percent >= 25:
        return "It is badly wounded."
    elif percent > 0:
        return "It looks close to death."
    else:
        return "It appears to be dead."


def _describe_mana(current_mp: int, max_mp: int) -> str | None:
    """Generate a mana/magical presence description."""
    if max_mp <= 0:
        return None

    percent = (current_mp / max_mp) * 100

    if percent >= 75:
        return "Magical energy crackles around it."
    elif percent >= 50:
        return "A faint magical aura surrounds it."
    elif percent >= 25:
        return "Its magical presence feels diminished."
    else:
        # Low mana isn't visually obvious
        return None


def _describe_stats(stats: Stats) -> str | None:
    """Generate descriptions for notably high or low stats."""
    observations: list[str] = []

    # High stats (14+)
    HIGH_THRESHOLD = 14
    # Low stats (7-)
    LOW_THRESHOLD = 7

    # Check each stat for notable values
    if stats.strength >= HIGH_THRESHOLD:
        observations.append("It looks very strong.")
    elif stats.strength <= LOW_THRESHOLD:
        observations.append("It looks physically weak.")

    if stats.dexterity >= HIGH_THRESHOLD:
        observations.append("It moves with fluid grace.")
    elif stats.dexterity <= LOW_THRESHOLD:
        observations.append("It appears clumsy.")

    if stats.constitution >= HIGH_THRESHOLD:
        observations.append("It looks hardy and resilient.")

    if stats.intelligence >= HIGH_THRESHOLD:
        observations.append("It has an intelligent gleam in its eyes.")
    elif stats.intelligence <= LOW_THRESHOLD:
        observations.append("It has a dull, vacant look.")

    if stats.wisdom >= HIGH_THRESHOLD:
        observations.append("It watches you with knowing eyes.")

    if stats.charisma >= HIGH_THRESHOLD:
        observations.append("It has a commanding presence.")

    # Limit to 2 most notable observations to avoid text bloat
    if len(observations) > 2:
        observations = observations[:2]

    if observations:
        return " ".join(observations)
    return None
