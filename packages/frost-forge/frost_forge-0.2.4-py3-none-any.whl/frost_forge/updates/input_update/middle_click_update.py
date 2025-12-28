from ...info import UI_SCALE, SCREEN_SIZE, ACCESSORIES


def middle_click(position, inventory_size, inventory, accessory):
    if position[1] >= SCREEN_SIZE[1] - 32 * UI_SCALE:
        moved_x = position[0] - SCREEN_SIZE[0] // 2
        if abs(moved_x) <= 16 * inventory_size[0] * UI_SCALE:
            slot_number = (
                (moved_x - 16 * UI_SCALE * (inventory_size[0] % 2)) // (32 * UI_SCALE)
                + inventory_size[0] // 2
                + inventory_size[0] % 2
            )
            if slot_number < len(inventory):
                item = list(inventory.items())[slot_number]
                if item[0] in ACCESSORIES and item[0] not in accessory:
                    print("5")
                    accessory.append(item[0])
                    inventory[item[0]] -= 1
                    if inventory[item[0]] == 0:
                        del inventory[item[0]]
        elif position[0] <= 96 * UI_SCALE:
            slot_number = position[0] // (32 * UI_SCALE)
            if slot_number < len(accessory):
                item = accessory[slot_number]
                inventory[item] = inventory.get(item, 0) + 1
                accessory.pop(slot_number)
    return inventory, accessory