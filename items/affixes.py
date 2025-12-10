import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from ecs.components import Component

if TYPE_CHECKING:
    from ecs.world import World


@dataclass
class Affix:
    """A modifier that can be applied to items"""

    name: str
    affix_type: str  # "prefix" or "suffix"
    stat_modifiers: dict[str, int] = field(default_factory=dict)
    rarity_weight: int = 100  # Higher = more common when rolling


WEAPON_PREFIXES: list[Affix] = [
    Affix("Sharp", "prefix", {"damage": 2}, rarity_weight=100),
    Affix("Keen", "prefix", {"damage": 3}, rarity_weight=75),
    Affix("Mighty", "prefix", {"strength": 2}, rarity_weight=80),
    Affix("Swift", "prefix", {"dexterity": 2}, rarity_weight=80),
    Affix("Brutal", "prefix", {"damage": 4, "defense": -1}, rarity_weight=50),
    Affix("Vicious", "prefix", {"damage": 3, "strength": 1}, rarity_weight=40),
    Affix("Fine", "prefix", {"damage": 1, "dexterity": 1}, rarity_weight=90),
]

WEAPON_SUFFIXES: list[Affix] = [
    Affix("of Power", "suffix", {"strength": 1, "damage": 1}, rarity_weight=100),
    Affix("of the Bear", "suffix", {"strength": 3}, rarity_weight=70),
    Affix("of the Fox", "suffix", {"dexterity": 3}, rarity_weight=70),
    Affix("of Precision", "suffix", {"dexterity": 2, "damage": 1}, rarity_weight=60),
    Affix(
        "of the Giant", "suffix", {"strength": 4, "constitution": 1}, rarity_weight=30
    ),
    Affix("of Fury", "suffix", {"damage": 2, "strength": 2}, rarity_weight=40),
    Affix("of Skill", "suffix", {"dexterity": 2}, rarity_weight=90),
]

ARMOR_PREFIXES: list[Affix] = [
    Affix("Sturdy", "prefix", {"defense": 2}, rarity_weight=100),
    Affix("Reinforced", "prefix", {"defense": 3}, rarity_weight=75),
    Affix("Hardy", "prefix", {"constitution": 2}, rarity_weight=80),
    Affix("Protective", "prefix", {"defense": 2, "max_hp": 5}, rarity_weight=50),
    Affix("Thick", "prefix", {"defense": 1, "constitution": 1}, rarity_weight=90),
    Affix("Rugged", "prefix", {"defense": 2, "constitution": 1}, rarity_weight=60),
    Affix("Enchanted", "prefix", {"defense": 1, "intelligence": 2}, rarity_weight=40),
]

ARMOR_SUFFIXES: list[Affix] = [
    Affix("of the Ox", "suffix", {"constitution": 3}, rarity_weight=70),
    Affix(
        "of Fortitude", "suffix", {"constitution": 2, "defense": 2}, rarity_weight=50
    ),
    Affix("of the Sage", "suffix", {"intelligence": 3}, rarity_weight=70),
    Affix("of Warding", "suffix", {"defense": 3}, rarity_weight=75),
    Affix("of the Owl", "suffix", {"wisdom": 3}, rarity_weight=70),
    Affix("of Vitality", "suffix", {"max_hp": 10, "constitution": 1}, rarity_weight=40),
    Affix("of the Turtle", "suffix", {"defense": 2, "max_hp": 5}, rarity_weight=60),
    Affix("of Grace", "suffix", {"dexterity": 2, "charisma": 1}, rarity_weight=80),
]


@dataclass
class ItemAffixes(Component):
    """Affixes applied to an item"""

    prefix: Optional[Affix] = None
    suffix: Optional[Affix] = None

    def get_total_modifiers(self) -> dict[str, int]:
        """Combine all affix stat modifiers"""
        totals: dict[str, int] = {}
        for affix in [self.prefix, self.suffix]:
            if affix:
                for stat, value in affix.stat_modifiers.items():
                    totals[stat] = totals.get(stat, 0) + value
        return totals

    def get_display_name(self, base_name: str) -> str:
        """Generate name like 'Mighty Sword of the Bear'"""
        name = base_name
        if self.prefix:
            name = f"{self.prefix.name} {name}"
        if self.suffix:
            name = f"{name} {self.suffix.name}"
        return name


def roll_affix(pool: list[Affix]) -> Affix:
    """Randomly select an affix from a pool based on rarity weights"""
    total_weight = sum(affix.rarity_weight for affix in pool)
    roll = random.randint(1, total_weight)

    current_weight = 0
    for affix in pool:
        current_weight += affix.rarity_weight
        if roll <= current_weight:
            return affix

    return pool[0]


def get_affix_pool(slot: str, affix_type: str) -> list[Affix]:
    """Get the appropriate affix pool for an equipment slot"""
    is_weapon = slot in ("main_hand", "off_hand", "two_hand")

    if affix_type == "prefix":
        return WEAPON_PREFIXES if is_weapon else ARMOR_PREFIXES
    else:
        return WEAPON_SUFFIXES if is_weapon else ARMOR_SUFFIXES


def apply_affixes_for_rarity(
    world: "World", item_id: int, rarity: str, slot: str
) -> None:
    """Apply appropriate affixes based on rarity"""
    if rarity == "common":
        # No affixes for common items
        return

    prefix: Optional[Affix] = None
    suffix: Optional[Affix] = None

    if rarity == "uncommon":
        # Roll prefix OR suffix (50/50)
        if random.random() < 0.5:
            prefix = roll_affix(get_affix_pool(slot, "prefix"))
        else:
            suffix = roll_affix(get_affix_pool(slot, "suffix"))

    elif rarity in ("rare", "epic", "legendary"):
        # Roll both prefix AND suffix
        prefix = roll_affix(get_affix_pool(slot, "prefix"))
        suffix = roll_affix(get_affix_pool(slot, "suffix"))

    if prefix or suffix:
        world.add_component(item_id, ItemAffixes(prefix=prefix, suffix=suffix))
