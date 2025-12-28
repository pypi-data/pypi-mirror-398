import os

from ..info import SETTINGS_FILE, DEFAULT_CONTROLS


def settings_load():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            controls = [int(i) for i in file.read().split(";")[0].split(":") if i]
    else:
        controls = [
            *DEFAULT_CONTROLS,
        ]
    return controls


def settings_save(controls):
    control_str = ""
    for i in controls:
        control_str += f"{i}:"
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        file.write(f"{control_str}")
