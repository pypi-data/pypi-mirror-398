def take_out(chunks, location, inventory, slot_number, machine_inventory, inventory_size, singular=False):
    if slot_number < len(machine_inventory):
        item = list(machine_inventory.items())[slot_number]
        if singular:
            item = (item[0], 1)
        inventory_item = inventory.get(item[0], 0)
        if not (inventory_item == 0 and len(inventory) == inventory_size[0]):
            if inventory_item + item[1] <= inventory_size[1]:
                inventory[item[0]] = inventory_item + item[1]
                if not singular:
                    del chunks[location["opened"][0]][location["opened"][1]][
                        "inventory"
                    ][item[0]]
                else:
                    chunks[location["opened"][0]][location["opened"][1]]["inventory"][
                        item[0]
                    ] -= 1
                    if (
                        chunks[location["opened"][0]][location["opened"][1]][
                            "inventory"
                        ][item[0]]
                        == 0
                    ):
                        del chunks[location["opened"][0]][location["opened"][1]][
                            "inventory"
                        ][item[0]]
            else:
                inventory[item[0]] = inventory_size[1]
                chunks[location["opened"][0]][location["opened"][1]]["inventory"][
                    item[0]
                ] = inventory_item + item[1] - inventory_size[1]
        if chunks[location["opened"][0]][location["opened"][1]]["inventory"] == {}:
            del chunks[location["opened"][0]][location["opened"][1]]["inventory"]
    return chunks
