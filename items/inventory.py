from typing import TYPE_CHECKING

from ecs.components import Inventory, Position
from items.components import InInventory, Item, OnGround

if TYPE_CHECKING:
    from ecs.world import World


def get_inventory_items(world: "World", owner: int) -> list[int]:
    items: set[int] = world.get_entities_with(InInventory, Item)
    return [
        item_id
        for item_id in items
        if world.component_for(item_id, InInventory).owner == owner
    ]


def get_items_at_position(world: "World", x: int, y: int) -> list[int]:
    items: set[int] = world.get_entities_with(OnGround, Position, Item)
    result: list[int] = []
    for item_id in items:
        pos: Position = world.component_for(item_id, Position)
        if pos.x == x and pos.y == y:
            result.append(item_id)

    return result


def get_used_slots(world: "World", owner: int) -> int:
    items: list[int] = get_inventory_items(world, owner)
    total: int = 0
    for item_id in items:
        item: Item = world.component_for(item_id, Item)
        total += item.slot_size
    return total


def get_free_slots(world: "World", owner: int) -> int:
    inventory: Inventory = world.component_for(owner, Inventory)
    return inventory.max_slots - get_used_slots(world, owner)


def can_pickup(world: "World", owner: int, item_id: int) -> bool:
    item: Item = world.component_for(item_id, Item)
    return get_free_slots(world, owner) >= item.slot_size


def pickup_item(world: "World", owner: int, item_id: int) -> bool:
    if not can_pickup(world, owner, item_id):
        return False

    # Remove the components that make the item appear on the game map
    world.remove_component(item_id, OnGround)
    world.remove_component(item_id, Position)

    world.add_component(item_id, InInventory(owner=owner))
    return True


def drop_item(world: "World", owner: int, item_id: int, x: int, y: int) -> bool:
    in_inventory: InInventory = world.component_for(item_id, InInventory)
    if not in_inventory or in_inventory.owner != owner:
        return False

    # Remove the component marking this item in inventory
    world.remove_component(item_id, InInventory)

    # Add the item entity to the game map
    world.add_component(item_id, OnGround())
    world.add_component(item_id, Position(x=x, y=y))
    return True
