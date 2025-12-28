from math import pi, cos

import pygame as pg

from ...info import TILE_SIZE, HALF_SIZE, CHUNK_SIZE, SCREEN_SIZE, MULTI_TILES, FLOOR, DAY_LENGTH
from ..game_rendering import (
    render_ghost,
    render_mined,
    render_hand,
    render_map,
)


def render_game(
    chunks,
    location,
    zoom,
    inventory,
    inventory_number,
    tick,
    camera,
    position,
    window,
    images,
):
    window.fill((206, 229, 242))
    player_pixel_position = (
        location["real"][2] * TILE_SIZE + location["real"][0] * CHUNK_SIZE + HALF_SIZE,
        location["real"][3] * TILE_SIZE + location["real"][1] * CHUNK_SIZE + HALF_SIZE,
    )
    camera = (
        (player_pixel_position[0] + position[0] / 4 / zoom) * 0.2 + camera[0] * 0.8,
        (player_pixel_position[1] + position[1] / 4 / zoom) * 0.2 + camera[1] * 0.8,
    )
    zoom_camera = (SCREEN_SIZE[0] * 5 / 8 - camera[0] * zoom, SCREEN_SIZE[1] * 5 / 8 - camera[1] * zoom)
    scaled_image = {}
    for image in images:
        if image in FLOOR:
            scaled_image[image] = pg.transform.scale(
                images[image], ((TILE_SIZE + 2) * zoom, (TILE_SIZE + 2) * zoom)
            )
        else:
            size = MULTI_TILES.get(image, (1, 1))
            scaled_image[image] = pg.transform.scale(
                images[image],
                (
                    (TILE_SIZE * size[0] + 2) * zoom,
                    ((size[1] + 1 / 2) * TILE_SIZE + 2) * zoom,
                ),
            )
    window = render_map(location, chunks, zoom_camera, zoom, scaled_image, window, images)
    window = render_hand(
        inventory, inventory_number, zoom_camera, location, zoom, window, images
    )
    window = render_ghost(
        position,
        zoom_camera,
        zoom,
        chunks,
        location,
        inventory,
        inventory_number,
        scaled_image,
        window,
    )
    dark_overlay = pg.Surface(SCREEN_SIZE)
    dark_overlay.fill((19, 17, 18))
    dark_overlay.set_alpha(int((1 - cos(((tick / DAY_LENGTH * 2) - 1 / 2) * pi)) * 95))
    window.blit(dark_overlay, (0, 0))
    window = render_mined(location["mined"], chunks, zoom_camera, zoom, window, images)
    return camera, window
