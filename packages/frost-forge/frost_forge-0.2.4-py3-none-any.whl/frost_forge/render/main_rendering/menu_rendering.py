import os

import pygame as pg

from ...info import SCREEN_SIZE, WORLD_TYPES, CONTROL_NAMES, SAVES_FOLDER, TEXT_DISTANCE
from .menu_text import render_text

pg.font.init()


def render_menu(
    menu_placement: str,
    save_file_name: str,
    controls: list,
    window,
    scroll,
    control_adjusted,
    world_type,
    seed,
    images,
):
    window.fill((206, 229, 242))
    if menu_placement == "load_save":
        render_text(window, "Back to menu", 0, images)
        render_text(window, "Create new world", 1, images)

        saves = [f[: -len(".txt")] for f in os.listdir(SAVES_FOLDER)]
        for i, save in enumerate(saves):
            render_text(window, f"[x] [{save.capitalize()}]", 2 + i, images)

    elif menu_placement == "save_creation":
        render_text(window, "Name your new save?", 0, images)
        render_text(window, save_file_name.capitalize(), 1, images)
        render_text(window, "Proceed", 2, images)
        render_text(window, "Don't save", 3, images)

    elif menu_placement == "save_options":
        render_text(window, "Back to save selection", 0, images)
        render_text(window, "Create new save", 1, images)
        render_text(
            window, f"World type: {WORLD_TYPES[world_type].capitalize()}", 2, images
        )
        render_text(window, f"World seed: {seed.capitalize()}", 3, images)

    elif menu_placement.split("_")[0] == "options":
        if menu_placement == "options_game":
            render_text(window, "Return to game", 0, images)
            render_text(window, "Save and Quit", 2, images)
        elif menu_placement == "options_main":
            render_text(window, "Back to menu", 0, images)
        render_text(window, "Controls options", 1, images)

    elif menu_placement == "main_menu":
        render_text(window, "Welcome to Frost Forge", 0, images)
        render_text(window, "Play", 1, images)
        render_text(window, "Options", 2, images)
        render_text(window, "Credits", 3, images)
        render_text(window, "Quit Game", 4, images)

    elif menu_placement == "controls_options":
        pg.draw.rect(
            window,
            (181, 102, 60),
            pg.Rect(0, TEXT_DISTANCE * (control_adjusted - scroll), SCREEN_SIZE[0], 50),
        )
        for y in range(len(controls)):
            render_text(
                window,
                f"{CONTROL_NAMES[y]}: {pg.key.name(controls[y]).capitalize()}",
                y - scroll,
                images,
            )

    elif menu_placement == "credits":
        render_text(window, "Back to menu", 0, images)
        render_text(window, "Game developer: TimoAndy08", 1, images)
        render_text(window, "Special thanks to: Havsalt", 2, images)
        render_text(window, "Gamebreaker: Sonus", 3, images)
    return window
