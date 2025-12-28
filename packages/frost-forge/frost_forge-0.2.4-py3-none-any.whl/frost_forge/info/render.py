import os

import pygame as pg


pg.display.init()
pg.font.init()

SCREEN_SIZE = (pg.display.Info().current_w, pg.display.Info().current_h)
TILE_SIZE = 64
HALF_SIZE = TILE_SIZE // 2
CHUNK_SIZE = 16 * TILE_SIZE
FPS = 60
DAY_LENGTH = 60 * 24 * FPS
UI_SCALE = 2
UI_FONT = pg.font.SysFont("Lucida Console", 10 * UI_SCALE)
BIG_UI_FONT = pg.font.SysFont("Lucida Console", 20 * UI_SCALE)
SLOT_SIZE = (32 * UI_SCALE, 32 * UI_SCALE)
TILE_UI_SIZE = (16 * UI_SCALE, 24 * UI_SCALE)
FLOOR_SIZE = (16 * UI_SCALE, 16 * UI_SCALE)
HALF_SCREEN_SIZE = SCREEN_SIZE[0] // 2
BIG_SLOT_SIZE = (96 * UI_SCALE, 96 * UI_SCALE)
BIG_SLOT_PLACEMENT = (HALF_SCREEN_SIZE - 128 * UI_SCALE, SCREEN_SIZE[1] - 144 * UI_SCALE)
TEXT_DISTANCE = 75
SETTINGS_FILE = os.path.normpath(os.path.join(__file__, "../../..", "settings.txt"))
SAVES_FOLDER = os.path.normpath(os.path.join(__file__, "../../..", "saves"))
CONTROL_NAMES = (
    "Move up ",
    "Move left ",
    "Move down ",
    "Move right",
    "Inventory ",
    "Zoom in",
    "Zoom out",
    "Slot 1",
    "Slot 2",
    "Slot 3",
    "Slot 4",
    "Slot 5",
    "Slot 6",
    "Slot 7",
    "Slot 8",
    "Slot 9",
    "Slot 10",
    "Slot 11",
    "Slot 12",
    "Hotbar scroll right",
    "Hotbar scroll left",
    "Go to menu",
    "Menu scroll down",
    "Menu scroll up",
    "Sneak",
)
DEFAULT_CONTROLS = (
    pg.K_w,
    pg.K_a,
    pg.K_s,
    pg.K_d,
    pg.K_e,
    pg.K_z,
    pg.K_x,
    pg.K_1,
    pg.K_2,
    pg.K_3,
    pg.K_4,
    pg.K_5,
    pg.K_6,
    pg.K_7,
    pg.K_8,
    pg.K_9,
    pg.K_0,
    pg.K_PLUS,
    pg.K_BACKSLASH,
    pg.K_RIGHT,
    pg.K_LEFT,
    pg.K_TAB,
    pg.K_DOWN,
    pg.K_UP,
    pg.K_LCTRL,
)

if not os.path.exists(SAVES_FOLDER):
    os.makedirs(SAVES_FOLDER)
