from ...info import TILE_SIZE, ATTRIBUTES, RECIPES, SCREEN_SIZE
from .right_click_updates import right_click
from .left_click_update import left_click
from .middle_click_update import middle_click


def button_press(
    button,
    position,
    zoom,
    chunks,
    location,
    machine_ui,
    inventory,
    health,
    max_health,
    machine_inventory,
    tick,
    inventory_number,
    recipe_number,
    camera,
    inventory_size,
    world_type,
    accessory,
):
    world_x = (position[0] - SCREEN_SIZE[0] * 5 / 8 + camera[0] * zoom) // (TILE_SIZE * zoom)
    world_y = (position[1] - SCREEN_SIZE[1] * 5 / 8 + camera[1] * zoom) // (TILE_SIZE * zoom)
    if (world_x - location["tile"][0] * 16 - location["tile"][2]) ** 2 + (
        world_y - location["tile"][1] * 16 - location["tile"][3]
    ) ** 2 <= 10 or "open" in ATTRIBUTES.get(machine_ui, ()):
        grid_position = [(world_x // 16, world_y // 16), (world_x % 16, world_y % 16)]
        if (
            grid_position[1] in chunks[grid_position[0]]
            and "kind" in chunks[grid_position[0]][grid_position[1]]
        ):
            while "point" in ATTRIBUTES.get(
                chunks[grid_position[0]][grid_position[1]]["kind"], ()
            ):
                if chunks[grid_position[0]][grid_position[1]]["kind"] == "left":
                    grid_position = [
                        (
                            grid_position[0][0] - (grid_position[1][0] == 0),
                            grid_position[0][1],
                        ),
                        ((grid_position[1][0] - 1) % 16, grid_position[1][1]),
                    ]
                elif chunks[grid_position[0]][grid_position[1]]["kind"] == "up":
                    grid_position = [
                        (
                            grid_position[0][0],
                            grid_position[0][1] - (grid_position[1][1] == 0),
                        ),
                        (grid_position[1][0], (grid_position[1][1] - 1) % 16),
                    ]

        if button == 1:
            (
                machine_ui,
                chunks,
                location,
                machine_inventory,
                tick,
                health,
                max_health,
                inventory,
                recipe_number,
            ) = left_click(
                machine_ui,
                grid_position,
                chunks,
                inventory_number,
                health,
                max_health,
                position,
                recipe_number,
                location,
                inventory,
                machine_inventory,
                tick,
                inventory_size,
                world_type,
            )
        elif button == 3:
            chunks, location, machine_ui, machine_inventory, health, inventory = right_click(
                chunks,
                grid_position,
                inventory,
                inventory_number,
                location,
                machine_ui,
                position,
                machine_inventory,
                health,
                inventory_size,
            )

    if button == 2:
        inventory, accessory = middle_click(position, inventory_size, inventory, accessory)
    elif button == 4 or button == 5:
        if "craft" in ATTRIBUTES.get(machine_ui, ()) or "machine" in ATTRIBUTES.get(
            machine_ui, ()
        ):
            recipe_number = (recipe_number + (button == 5) - (button == 4)) % len(RECIPES[machine_ui])
        else:
            inventory_number = (
                inventory_number + (button == 5) - (button == 4)
            ) % inventory_size[0]
    return (
        chunks,
        location,
        machine_ui,
        machine_inventory,
        tick,
        inventory_number,
        health,
        max_health,
        inventory,
        recipe_number,
        accessory,
    )
