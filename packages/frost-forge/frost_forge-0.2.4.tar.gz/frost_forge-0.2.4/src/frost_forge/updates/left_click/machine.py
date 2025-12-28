from ...info import (
    SCREEN_SIZE,
    UI_SCALE,
    RECIPES,
    LOOT_TABLES,
    MACHINES,
    VALUES,
)
from .put_in import put_in
from .take_out import take_out


def machine_storage(position, chunks, location, inventory, machine_ui, inventory_size, singular=False):
    if "inventory" not in chunks[location["opened"][0]][location["opened"][1]]:
        chunks[location["opened"][0]][location["opened"][1]]["inventory"] = {}
    moved_x = position[0] - SCREEN_SIZE[0] // 2
    machine = chunks[location["opened"][0]][location["opened"][1]]
    machine_recipe = RECIPES[machine_ui][machine.get("recipe", 0)]
    holding_over_inventory = (
        position[1] >= SCREEN_SIZE[1] - 32 * UI_SCALE
        and abs(moved_x) <= 16 * inventory_size[0] * UI_SCALE
    )
    if holding_over_inventory:
        inventory_number = (
            (moved_x - 16 * UI_SCALE * (inventory_size[0] % 2)) // (32 * UI_SCALE)
            + inventory_size[0] // 2
            + inventory_size[0] % 2
        )
        if inventory_number < len(inventory):
            item = list(inventory.items())[inventory_number]
            may_put_in = False
            if machine["kind"] in MACHINES:
                i = 0
                for value_item in MACHINES[machine["kind"]]:
                    if item[0] in VALUES[value_item]:
                        may_put_in = True
                        convertion_inventory = list(inventory.items())
                        if singular:
                            convertion_inventory.append((convertion_inventory[inventory_number][0], convertion_inventory[inventory_number][1] - 1))
                            convertion_inventory[inventory_number] = (MACHINES[machine["kind"]][i], VALUES[value_item][item[0]])
                            singular = False
                        else:
                            convertion_inventory[inventory_number] = (MACHINES[machine["kind"]][i], item[1] * VALUES[value_item][item[0]])
                        inventory = dict(convertion_inventory)
                        if inventory.get(item[0], -1) == 0:
                            del inventory[item[0]]
                        break
                    i += 1
            for i in range(0, len(machine_recipe[1])):
                if machine_recipe[1][i][0] == item[0]:
                    may_put_in = True
            if may_put_in:
                chunks = put_in(
                    chunks,
                    location,
                    inventory,
                    (14, 64),
                    inventory_number,
                    machine["inventory"],
                    singular,
                )
    slot_row = (position[1] - SCREEN_SIZE[1] + 144 * UI_SCALE) // (32 * UI_SCALE)
    slot_column = (moved_x + 112 * UI_SCALE) // (32 * UI_SCALE)
    item = [machine_recipe[0][0], machine["inventory"].get(machine_recipe[0][0], 0)]
    if slot_row == 2 and (slot_column == 0 or (item[0] in LOOT_TABLES and slot_column < len(LOOT_TABLES[item[0]]))):
        if item[0] in LOOT_TABLES:
            item[0] = LOOT_TABLES[item[0]][0][slot_column][1]
        if item[0] in machine["inventory"]:
            checking_inventory = list(machine["inventory"])
            for i in range(len(checking_inventory)):
                if checking_inventory[i] == item[0]:
                    slot_number = i
            chunks = take_out(chunks, location, inventory, slot_number, machine["inventory"], inventory_size, singular)
    return chunks, inventory
