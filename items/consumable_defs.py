"""
Consumable item template definitions.

This module provides a centralized registry of consumable item templates,
making it easy to add new items without modifying factory code.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ConsumableTemplate:
    """Template for creating consumable items."""

    name: str
    glyph: str
    color: str
    effect_type: str
    power: int = 0
    base_value: int = 10
    duration: int = 0  # 0 = instant, >0 = lasts N turns
    stat_modifiers: dict[str, int] = field(default_factory=dict)
    creates_pool: bool = False
    pool_name: str | None = None
    radius: int = 0  # 0 = single target, >0 = AoE


# Consumable type for type hints
ConsumableType = Literal[
    # Potions
    "health_potion",
    "mana_potion",
    "potion_of_strength",
    "potion_of_dexterity",
    "potion_of_intelligence",
    "potion_of_regeneration",
    "potion_of_poison",
    # Scrolls
    "scroll_of_fireball",
    "scroll_of_mass_healing",
    "scroll_of_flood",
]


# Template registry
CONSUMABLE_TEMPLATES: dict[str, ConsumableTemplate] = {
    # Potions use '!' glyph and create pools when thrown
    "health_potion": ConsumableTemplate(
        name="Health Potion",
        glyph="!",
        color="red",
        effect_type="heal",
        power=20,
        base_value=25,
        creates_pool=True,
    ),
    "mana_potion": ConsumableTemplate(
        name="Mana Potion",
        glyph="!",
        color="blue",
        effect_type="restore_mana",
        power=15,
        base_value=25,
        creates_pool=True,
    ),
    "potion_of_strength": ConsumableTemplate(
        name="Potion of Strength",
        glyph="!",
        color="orange",
        effect_type="stat_buff",
        power=0,
        base_value=40,
        duration=20,
        stat_modifiers={"strength": 3},
        creates_pool=True,
    ),
    "potion_of_dexterity": ConsumableTemplate(
        name="Potion of Dexterity",
        glyph="!",
        color="yellow",
        effect_type="stat_buff",
        power=0,
        base_value=40,
        duration=20,
        stat_modifiers={"dexterity": 3},
        creates_pool=True,
    ),
    "potion_of_intelligence": ConsumableTemplate(
        name="Potion of Intelligence",
        glyph="!",
        color="purple",
        effect_type="stat_buff",
        power=0,
        base_value=40,
        duration=20,
        stat_modifiers={"intelligence": 3},
        creates_pool=True,
    ),
    "potion_of_regeneration": ConsumableTemplate(
        name="Potion of Regeneration",
        glyph="!",
        color="green",
        effect_type="regen",
        power=3,  # Heals 3 HP per turn
        base_value=35,
        duration=10,
        creates_pool=True,
    ),
    "potion_of_poison": ConsumableTemplate(
        name="Potion of Poison",
        glyph="!",
        color="dark green",
        effect_type="poison",
        power=5,  # 5 damage per turn
        base_value=30,
        duration=5,
        creates_pool=True,
        pool_name="poisonous liquid",
    ),
    # Scrolls use '?' glyph and typically don't create pools (unless specified)
    "scroll_of_fireball": ConsumableTemplate(
        name="Scroll of Fireball",
        glyph="?",
        color="orange",
        effect_type="damage",
        power=15,
        base_value=50,
        radius=2,
    ),
    "scroll_of_mass_healing": ConsumableTemplate(
        name="Scroll of Mass Healing",
        glyph="?",
        color="light green",
        effect_type="heal",
        power=10,
        base_value=40,
        radius=1,
    ),
    "scroll_of_flood": ConsumableTemplate(
        name="Scroll of Flood",
        glyph="?",
        color="blue",
        effect_type="damage",
        power=0,
        base_value=60,
        radius=2,
        creates_pool=True,
        pool_name="water",
    ),
}


def get_template(template_id: str) -> ConsumableTemplate | None:
    """Get a consumable template by ID."""
    return CONSUMABLE_TEMPLATES.get(template_id)


def list_templates() -> list[str]:
    """List all available template IDs."""
    return list(CONSUMABLE_TEMPLATES.keys())
