from ...info import FOOD, FLOOR, HEALTH_INCREASE, INVENTORY_INCREASE, MODIFICATIONS
from ...other_systems.tile_placement import place_tile
from ...other_systems.tile_placable import is_placable


def place(
    inventory,
    inventory_key,
    is_tile,
    health,
    max_health,
    grid_position,
    chunks,
    inventory_size,
):
    if inventory_key not in inventory:
        return chunks, health, max_health, inventory_size
    if inventory_key not in FLOOR:
        if inventory_key in FOOD and health < max_health:
            health = min(health + FOOD[inventory_key], max_health)
        elif (
            inventory_key in HEALTH_INCREASE
            and HEALTH_INCREASE[inventory_key][0]
            <= max_health
            < HEALTH_INCREASE[inventory_key][1]
        ):
            max_health += HEALTH_INCREASE[inventory_key][2]
            health += HEALTH_INCREASE[inventory_key][2]
        elif inventory_key in INVENTORY_INCREASE and INVENTORY_INCREASE[inventory_key][0] == inventory_size[0]:
            inventory_size[0] += INVENTORY_INCREASE[inventory_key][1]
        elif is_tile and inventory_key.split(" ")[-1] == "wrench" and chunks[grid_position[0]][grid_position[1]]["floor"].split(" ")[-1].isdigit():
            floor = chunks[grid_position[0]][grid_position[1]]["floor"]
            new_floor = ""
            for word in floor.split(" ")[:-1]:
                new_floor += f"{word} "
            chunks[grid_position[0]][grid_position[1]]["floor"] = f"{new_floor}{(int(floor.split(" ")[-1]) + 1) % MODIFICATIONS[new_floor[:-1]]}"
            inventory[inventory_key] += 1
        elif is_placable(inventory_key, grid_position, chunks):
            chunks = place_tile(inventory_key, grid_position, chunks)
        else:
            inventory[inventory_key] += 1
        inventory[inventory_key] -= 1
    elif not is_tile:
        inventory[inventory_key] -= 1
        chunks[grid_position[0]][grid_position[1]] = {"floor": inventory_key}
    if inventory[inventory_key] == 0:
        del inventory[inventory_key]
    return chunks, health, max_health, inventory_size
