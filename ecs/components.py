from dataclasses import dataclass, field
from typing import Optional

from terminal.glyph import Glyph


class Component:
    pass


@dataclass
class IsPlayer(Component):
    pass


@dataclass
class IsActor(Component):
    pass


@dataclass
class TurnConsumed(Component):
    pass


@dataclass
class Position(Component):
    x: int
    y: int


@dataclass
class Drawable(Component):
    glyph: Glyph
    name: str


@dataclass
class Description(Component):
    """Base narrative description of an entity."""

    text: str


@dataclass
class MoveIntent(Component):
    dx: int
    dy: int
    consumes_turn: bool


@dataclass
class Stats(Component):
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10


@dataclass
class Health(Component):
    current_hp: int
    base_max_hp: int = 20  # Before constitution bonus applied

    def max_hp(self, stats: Stats, level: int) -> int:
        return self.base_max_hp + (stats.constitution * 2) + (level * 5)


@dataclass
class Mana(Component):
    current_mp: int
    base_max_mp: int = 10  # Before intelligence bonus applied

    def max_mp(self, stats: Stats, level: int) -> int:
        return self.base_max_mp + (stats.intelligence * 2) + (level * 3)


@dataclass
class Experience(Component):
    current_xp: int = 0
    level: int = 1

    def xp_for_next_level(self) -> int:
        # Triangualr level growth
        return self.level * (self.level + 1) * 50

    def xp_progress(self) -> tuple[int, int]:
        prev_threshold: int = (
            (self.level - 1) * self.level * 50 if self.level > 1 else 0
        )
        next_threshold: int = self.xp_for_next_level()
        return (self.current_xp - prev_threshold, next_threshold - prev_threshold)


@dataclass
class Inventory(Component):
    """
    Entity can hold items (consumables, equipment, treasure, etc)
    """

    max_slots: int = 20


@dataclass
class EquipmentSlots(Component):
    """
    Entity can equip items of type equipment
    """

    slots: dict[str, Optional[int]] = field(
        default_factory=lambda: {
            "head": None,
            "torso": None,
            "main_hand": None,
            "off_hand": None,
            "legs": None,
            "feet": None,
            "ring_1": None,
            "ring_2": None,
            "ring_3": None,
            "ring_4": None,
            "necklace": None,
            "cape": None,
        }
    )
