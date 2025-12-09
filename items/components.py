from dataclasses import dataclass

from ecs.components import Component


@dataclass
class Item(Component):
    item_type: str
    base_value: int = 0
    slot_size: int = 1
    identified: bool = False
    cursed: bool = False


@dataclass
class Consumable(Component):
    effect_type: str
    effect_power: int = 0
    uses_remaining: int = 1


@dataclass
class Equipment(Component):
    slot: str
    base_damage: int = 0
    base_defense: int = 0


@dataclass
class Treasure(Component):
    treasure_type: str


@dataclass
class OnGround(Component):
    """
    Flag component, indicates item is on ground, at position (has Position component)
    """

    pass


@dataclass
class InInventory(Component):
    owner: int  # Entity ID of owner


@dataclass
class Equipped(Component):
    owner: int  # Entity ID of owner
    slot: str
