from ...info import HEALTH, UNOBTAINABLE, VALUES
from .damage_calculation import calculate_damage


def break_tile(inventory, chunks, mining_tile, inventory_number, inventory_size):
    delete_mining_tile = False
    if "health" not in mining_tile:
        mining_tile["health"] = HEALTH[mining_tile["kind"]]
    mining_tile["health"] -= calculate_damage(
        mining_tile["kind"], inventory, inventory_number
    )
    if mining_tile["health"] <= 0:
        mining_floor_exist = "floor" in mining_tile
        if mining_floor_exist:
            mining_floor = mining_tile["floor"]
        junk_inventory = {}
        if "inventory" not in mining_tile:
            mining_tile["inventory"] = {}
        if mining_tile["kind"] not in UNOBTAINABLE:
            if mining_tile["kind"].split()[-1].isdigit():
                mining_tile["kind"] = mining_tile["kind"][:-1]
                mining_tile["kind"] += "0"
            mining_tile["inventory"][mining_tile["kind"]] = (
                mining_tile["inventory"].get(mining_tile["kind"], 0) + 1
            )
        for item, amount in mining_tile["inventory"].items():
            if item != "mana_level" and item not in VALUES:
                if item in inventory:
                    inventory[item] += amount
                    if inventory[item] > inventory_size[1]:
                        junk_inventory[item] = inventory[item] - inventory_size[1]
                        inventory[item] = inventory_size[1]
                else:
                    if len(inventory) < inventory_size[0]:
                        inventory[item] = amount
                    else:
                        junk_inventory[item] = amount
        if mining_floor_exist:
            mining_tile = {}
        else:
            delete_mining_tile = True
        if len(junk_inventory) > 0:
            mining_tile = {"kind": "junk", "inventory": junk_inventory}
        if mining_floor_exist:
            mining_tile["floor"] = mining_floor
    return chunks, delete_mining_tile, mining_tile
