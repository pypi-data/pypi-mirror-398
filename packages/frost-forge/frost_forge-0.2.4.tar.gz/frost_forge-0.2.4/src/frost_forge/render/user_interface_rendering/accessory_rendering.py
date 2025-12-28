import pygame as pg

from ...info import SLOT_SIZE, UI_SCALE, SCREEN_SIZE, TILE_UI_SIZE


def render_accessory(window, images, accessory):
    for i in range(0, 3):
        window.blit(
            pg.transform.scale(images["inventory_slot_3"], SLOT_SIZE), (32 * i * UI_SCALE, SCREEN_SIZE[1] - 32 * UI_SCALE),
        )
    t = 0
    for item in accessory:
        window.blit(
            pg.transform.scale(images[item], TILE_UI_SIZE), ((32 * t + 8) * UI_SCALE, SCREEN_SIZE[1] - 28 * UI_SCALE),
        )
        t += 1
    return window