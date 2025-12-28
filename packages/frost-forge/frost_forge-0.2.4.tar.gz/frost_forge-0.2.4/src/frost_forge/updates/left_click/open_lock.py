def unlock(inventory, inventory_number, chunks, grid_position):
    if len(inventory) > inventory_number:
        inventory_key = list(inventory.keys())[inventory_number]
        if inventory_key.split(" ")[-1] == "key":
            if (
                inventory_key.split()[0]
                == chunks[grid_position[0]][grid_position[1]]["kind"].split()[0]
            ):
                inventory[inventory_key] -= 1
                if inventory[inventory_key] == 0:
                    del inventory[inventory_key]
                del chunks[grid_position[0]][grid_position[1]]["kind"]
                if chunks[grid_position[0]][grid_position[1]] == {}:
                    del chunks[grid_position[0]][grid_position[1]]
    return chunks
