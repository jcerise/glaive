from dataclasses import dataclass, field

from ecs.components import Component


@dataclass
class Item(Component):
    item_type: str
    base_value: int = 0
    slot_size: int = 1
    identified: bool = False
    cursed: bool = False
    rarity: str = "common"  # common, uncommon, rare, epic, legendary


@dataclass
class Consumable(Component):
    effect_type: str
    effect_power: int = 0
    uses_remaining: int = 1
    creates_pool: bool = False  # If True, creates ground pool when thrown (potions/vials)
    radius: int = 0  # 0 = single target, >0 = AoE radius
    pool_name: str | None = None  # Custom pool name (e.g., "water"), uses default if None
    effect_duration: int = 0  # 0 = instant, >0 = duration in turns
    stat_modifiers: dict[str, int] = field(default_factory=dict)  # e.g., {"strength": 3}


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
