from ...info import RECIPES, LOOT_TABLES
from ...world_generation.loot_calculation import calculate_loot


def recipe(
    machine_ui: str,
    recipe_number: int,
    inventory: dict[str, int],
    inventory_size: list[int, int],
):
    output_item, output_amount = RECIPES[machine_ui][recipe_number][0]
    input = RECIPES[machine_ui][recipe_number][1]
    if (
        len(inventory) >= inventory_size[0]
        or inventory.get(output_item, 0) + output_amount > inventory_size[1]
    ):
        return inventory
    for i in range(0, len(input)):
        if input[i][0] not in inventory or inventory[input[i][0]] < input[i][1]:
            return inventory
    for i in range(0, len(input)):
        inventory[input[i][0]] -= input[i][1]
        if inventory[input[i][0]] <= 0:
            del inventory[input[i][0]]
    if output_item not in LOOT_TABLES:
        inventory[output_item] = inventory.get(output_item, 0) + output_amount
    else:
        loot = calculate_loot({"loot": output_item})
        if "inventory" in loot:
            for item in loot["inventory"]:
                inventory[item] = loot["inventory"][item] * output_amount + inventory.get(item, 0)
    return inventory
