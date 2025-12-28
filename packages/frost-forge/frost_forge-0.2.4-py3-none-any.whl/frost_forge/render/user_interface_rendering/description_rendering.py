from ...info import BIG_UI_FONT, UI_SCALE, DESCRIPTION


def render_description(window, inventory_number, inventory):
    if inventory_number < len(inventory):
        item = list(inventory.items())[inventory_number]
        window.blit(BIG_UI_FONT.render(str(item[0]).capitalize(), False, (19, 17, 18)), (0, 0))
        window.blit(BIG_UI_FONT.render(str(DESCRIPTION.get(item[0], "")), False, (19, 17, 18)), (0, 20 * UI_SCALE))
    return window