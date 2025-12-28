import pygame as pg

from ...info import (
    UI_SCALE,
    SCREEN_SIZE,
    BIG_UI_FONT,
    UI_FONT,
    SLOT_SIZE,
    BIG_SLOT_SIZE,
    BIG_SLOT_PLACEMENT,
    TILE_UI_SIZE,
    FLOOR_SIZE,
    HALF_SCREEN_SIZE,
    FLOOR,
)
from .store_rendering import render_store


def render_craft(window, current_recipes, images, recipe_number):
    if recipe_number >= 0:
        window.blit(pg.transform.scale(images["big_inventory_slot_2"], BIG_SLOT_SIZE), BIG_SLOT_PLACEMENT)
        product = current_recipes[recipe_number][0]
        size = (48 * UI_SCALE, (72 - 24 * (product[0] in FLOOR)) * UI_SCALE)
        placement = (HALF_SCREEN_SIZE - 104 * UI_SCALE, SCREEN_SIZE[1] - (132 - 24 * (product[0] in FLOOR)) * UI_SCALE)
        text_placement = (HALF_SCREEN_SIZE - 112 * UI_SCALE, SCREEN_SIZE[1] - 80 * UI_SCALE)
        window.blit(pg.transform.scale(images[product[0]], size), placement)
        window.blit(BIG_UI_FONT.render(str(product[1]), False, (19, 17, 18)), text_placement)
        input_list = current_recipes[recipe_number][1]
        for inputs in range(0, len(input_list)):
            position = [
                HALF_SCREEN_SIZE + (40 * (inputs % 4) - 32) * UI_SCALE,
                SCREEN_SIZE[1] + (32 * (inputs // 4) - 144) * UI_SCALE,
            ]
            window.blit(pg.transform.scale(images["inventory_slot"], SLOT_SIZE), position)
            position[0] += 8 * UI_SCALE
            position[1] += 4 * UI_SCALE
            if input_list[inputs][0] not in FLOOR:
                window.blit(pg.transform.scale(images[input_list[inputs][0]], TILE_UI_SIZE), position)
            else:
                window.blit(pg.transform.scale(images[input_list[inputs][0]], FLOOR_SIZE), (position[0], position[1] + 8 * UI_SCALE))
            position[1] += 28 * UI_SCALE
            window.blit(UI_FONT.render(str(input_list[inputs][1]), False, (19, 17, 18)), position)
    else:
        machine_inventory = {}
        for recipe in current_recipes:
            machine_inventory[recipe[0][0]] = recipe[0][1]
        window = render_store(window, len(current_recipes), images, machine_inventory)
    return window
