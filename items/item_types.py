from enum import Enum


class EquipmentSlot(Enum):
    HEAD = "head"
    TORSO = "torso"
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    LEGS = "legs"
    FEET = "feet"
    RING_1 = "ring_1"
    RING_2 = "ring_2"
    RING_3 = "ring_3"
    RING_4 = "ring_4"
    NECKLACE = "necklace"
    CAPE = "cape"


class ItemRarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


RARITY_COLORS = {
    "common": "white",
    "uncommon": "green",
    "rare": "light blue",
    "epic": "magenta",
    "legendary": "orange",
    "cursed": "red",
    "unidentified": "dark gray",
}
