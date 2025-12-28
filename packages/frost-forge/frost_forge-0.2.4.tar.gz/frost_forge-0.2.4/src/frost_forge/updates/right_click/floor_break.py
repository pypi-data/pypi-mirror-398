from ...info import HEALTH
from .damage_calculation import calculate_damage


def break_floor(mining_tile, inventory, inventory_number, inventory_size):
    delete_mining_tile = False
    if "health" not in mining_tile:
        mining_tile["health"] = HEALTH[mining_tile["floor"]]
    mining_tile["health"] -= calculate_damage(
        mining_tile["floor"], inventory, inventory_number
    )
    broke = False
    if mining_tile["health"] <= 0:
        if mining_tile["floor"] in inventory:
            if inventory[mining_tile["floor"]] < inventory_size[1]:
                broke = True
        elif len(inventory) < inventory_size[0]:
            broke = True
    if broke:
        if mining_tile["floor"].split()[-1] == "open":
            mining_tile["floor"] = mining_tile["floor"][:-5]
        elif mining_tile["floor"].split()[-1].isdigit():
            mining_tile["floor"] = mining_tile["floor"][:-1]
            mining_tile["floor"] += "0"
        inventory[mining_tile["floor"]] = inventory.get(mining_tile["floor"], 0) + 1
        delete_mining_tile = True
    return delete_mining_tile, inventory, mining_tile
