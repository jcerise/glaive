from typing import TYPE_CHECKING, Optional

from ecs.components import EquipmentSlots
from items.components import Equipment, Equipped, InInventory, Item

if TYPE_CHECKING:
    from ecs.world import World


SLOT_DISPLAY_NAMES = {
    "head": "Head",
    "torso": "Torso",
    "main_hand": "Main Hand",
    "off_hand": "Off Hand",
    "legs": "Legs",
    "feet": "Feet",
    "ring_1": "Ring 1",
    "ring_2": "Ring 2",
    "ring_3": "Ring 3",
    "ring_4": "Ring 4",
    "necklace": "Necklace",
    "cape": "Cape",
}


SLOT_DISPLAY_ORDER = [
    "head",
    "necklace",
    "cape",
    "torso",
    "main_hand",
    "off_hand",
    "legs",
    "ring_1",
    "ring_2",
    "feet",
    "ring_3",
    "ring_4",
]


def get_equipped_item(world: "World", owner: int, slot: str) -> Optional[int]:
    """Get item entity ID in a specific equipment slot, or None if empty"""
    equip_slots: EquipmentSlots = world.component_for(owner, EquipmentSlots)
    if not equip_slots:
        return None
    return equip_slots.slots.get(slot)


def get_all_equipped_items(world: "World", owner: int) -> dict[str, Optional[int]]:
    """Get dict of all equipment slots and their item IDs"""
    equip_slots: EquipmentSlots = world.component_for(owner, EquipmentSlots)
    if not equip_slots:
        return {}
    return equip_slots.slots.copy()


def can_equip(world: "World", owner: int, item_id: int) -> tuple[bool, str]:
    """
    Check if item can be equipped.
    """
    # Check owner has equipment slots
    equip_slots: EquipmentSlots = world.component_for(owner, EquipmentSlots)
    if not equip_slots:
        return False, "Cannot equip item"

    # Check item is equipment
    equipment: Equipment = world.component_for(item_id, Equipment)
    if not equipment:
        return False, "Item is not equipment, cannot equip"

    # Check slot exists (handles ring slots specially)
    slot: str = equipment.slot
    if slot == "ring":
        # Find first empty ring slot, or use ring_1
        for ring_slot in ["ring_1", "ring_2", "ring_3", "ring_4"]:
            if equip_slots.slots.get(ring_slot) is None:
                return True, ""
        # All ring slots full, but can still replace
        return True, ""

    if slot not in equip_slots.slots:
        return False, f"No slot for {slot}"

    return True, ""


def find_available_slot(world: "World", owner: int, item_id: int) -> Optional[str]:
    """
    Find an appropriate slot for an item.
    For rings, finds first empty ring slot or returns ring_1.
    """
    equipment: Equipment = world.component_for(item_id, Equipment)
    if not equipment:
        return None

    equip_slots: EquipmentSlots = world.component_for(owner, EquipmentSlots)
    if not equip_slots:
        return None

    slot: str = equipment.slot

    # Handle ring slots specially
    if slot == "ring":
        for ring_slot in ["ring_1", "ring_2", "ring_3", "ring_4"]:
            if equip_slots.slots.get(ring_slot) is None:
                return ring_slot
        return "ring_1"  # Default to first ring slot if all full

    return slot


def equip_item(
    world: "World", owner: int, item_id: int, target_slot: Optional[str] = None
) -> Optional[int]:
    """
    Equip item from inventory to equipment slot.
    Returns previously equipped item ID if slot was occupied (moved to inventory).
    Returns None if slot was empty.
    """
    equip_slots: EquipmentSlots = world.component_for(owner, EquipmentSlots)

    # Determine target slot
    slot: str | None = target_slot or find_available_slot(world, owner, item_id)
    if not slot:
        return None

    # Check if slot is occupied
    previous_item_id: int | None = equip_slots.slots.get(slot)

    # If there's an item in the slot, move it to inventory
    if previous_item_id is not None:
        unequip_to_inventory(world, owner, slot)

    # Remove item from inventory
    world.remove_component(item_id, InInventory)

    # Add equipped component to item
    world.add_component(item_id, Equipped(owner=owner, slot=slot))

    # Update equipment slots
    equip_slots.slots[slot] = item_id

    return previous_item_id


def unequip_to_inventory(world: "World", owner: int, slot: str) -> Optional[int]:
    """
    Unequip item from slot and move to inventory.
    Returns item ID if successful, None if slot was empty or inventory full.
    """
    from items.inventory import get_free_slots

    equip_slots: EquipmentSlots = world.component_for(owner, EquipmentSlots)
    if not equip_slots:
        return None

    item_id: int | None = equip_slots.slots.get(slot)
    if item_id is None:
        return None

    # Check inventory has space
    item: Item = world.component_for(item_id, Item)
    if get_free_slots(world, owner) < item.slot_size:
        return None  # Inventory full

    # Remove equipped component
    world.remove_component(item_id, Equipped)

    # Add to inventory
    world.add_component(item_id, InInventory(owner=owner))

    # Clear equipment slot
    equip_slots.slots[slot] = None

    return item_id


def get_equipment_bonuses(world: "World", owner: int) -> dict[str, int]:
    """
    Calculate total stat bonuses from all equipped items.
    Returns dict like {"damage": 10, "defense": 5}
    This is super simple right now, just handles damage and defense
    Eventually, will handle stat increases and effects as well
    """
    bonuses = {"damage": 0, "defense": 0}

    equip_slots: EquipmentSlots = world.component_for(owner, EquipmentSlots)
    if not equip_slots:
        return bonuses

    for slot, item_id in equip_slots.slots.items():
        if item_id is not None:
            equipment: Equipment = world.component_for(item_id, Equipment)
            if equipment:
                bonuses["damage"] += equipment.base_damage
                bonuses["defense"] += equipment.base_defense

    return bonuses
