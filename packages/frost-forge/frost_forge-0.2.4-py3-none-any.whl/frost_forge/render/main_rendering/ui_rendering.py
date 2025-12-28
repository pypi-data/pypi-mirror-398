from ..user_interface_rendering import render_health, render_inventory, render_open, render_achievement, render_accessory, render_description


def render_ui(
    inventory_number,
    inventory,
    machine_ui,
    recipe_number,
    health,
    max_health,
    machine_inventory,
    window,
    images,
    achievement_popup,
    inventory_size,
    accessory,
):
    window = render_health(window, images, health, max_health)
    window = render_inventory(inventory_number, window, images, inventory, inventory_size)
    window = render_accessory(window, images, accessory)
    window = render_open(machine_ui, window, images, recipe_number, machine_inventory)
    window = render_description(window, inventory_number, inventory)
    if achievement_popup[0] > 0:
        window = render_achievement(achievement_popup[1], window, images)
    return window
