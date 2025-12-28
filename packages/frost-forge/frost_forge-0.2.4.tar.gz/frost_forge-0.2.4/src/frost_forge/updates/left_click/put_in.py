def put_in(
    chunks,
    location,
    inventory,
    machine_storage,
    slot_number,
    machine_inventory,
    singular=False,
):
    if slot_number < len(inventory):
        item = list(inventory.items())[slot_number]
        if singular:
            item = (item[0], 1)
        machine_item = machine_inventory.get(item[0], 0)
        if not (machine_item == 0 and len(machine_inventory) == machine_storage[0]):
            if machine_item + item[1] <= machine_storage[1]:
                chunks[location["opened"][0]][location["opened"][1]]["inventory"][
                    item[0]
                ] = machine_item + item[1]
                if not singular:
                    del inventory[item[0]]
                else:
                    inventory[item[0]] -= 1
                    if inventory[item[0]] == 0:
                        del inventory[item[0]]
            else:
                chunks[location["opened"][0]][location["opened"][1]]["inventory"][
                    item[0]
                ] = machine_storage[1]
                inventory[item[0]] = machine_item + item[1] - machine_storage[1]
    return chunks
