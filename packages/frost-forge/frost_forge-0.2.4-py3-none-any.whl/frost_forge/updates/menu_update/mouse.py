from .load_save import save_loading
from .create_save import save_creating
from .options import option
from ...info import SCREEN_SIZE, WORLD_TYPES, TEXT_DISTANCE
from ...other_systems.game_saving import save_game


def update_mouse(state, event, chunks):
    if state.menu_placement == "load_save":
        if state.position[1] <= 50:
            state.menu_placement = "main_menu"
        elif TEXT_DISTANCE <= state.position[1] <= TEXT_DISTANCE + 50:
            state.menu_placement = "save_options"
            state.world_type = 0
            state.seed = ""
        elif state.position[1] % 75 <= 50:
            chunks = save_loading(state, chunks)
    elif state.menu_placement.startswith("options"):
        option(state, chunks)

    elif state.menu_placement == "save_options":
        if state.position[1] <= 50:
            state.menu_placement = "load_save"
        if TEXT_DISTANCE <= state.position[1] <= TEXT_DISTANCE + 50:
            chunks = save_creating(state, chunks)
        elif TEXT_DISTANCE * 2 <= state.position[1] <= TEXT_DISTANCE * 2 + 50:
            state.world_type = (state.world_type + 1) % len(WORLD_TYPES)
    elif state.menu_placement == "save_creation":
        if (
            TEXT_DISTANCE * 2 <= state.position[1] <= TEXT_DISTANCE * 2 + 50
            and state.save_file_name != ""
            and state.save_file_name.split("_")[0] != "autosave"
        ):
            state.menu_placement = "main_menu"
            save_game(chunks, state, state.save_file_name)
            state.save_file_name = ""
            chunks = {}
        elif TEXT_DISTANCE * 3 <= state.position[1] <= TEXT_DISTANCE * 3 + 50:
            state.menu_placement = "main_menu"
            state.save_file_name = ""
            chunks = {}

    elif state.menu_placement == "main_menu":
        if TEXT_DISTANCE <= state.position[1] <= TEXT_DISTANCE + 50:
            state.menu_placement = "load_save"
        elif TEXT_DISTANCE * 2 <= state.position[1] <= TEXT_DISTANCE * 2 + 50:
            state.menu_placement = "options_main"
        elif TEXT_DISTANCE * 3 <= state.position[1] <= TEXT_DISTANCE * 3 + 50:
            state.menu_placement = "credits"
        elif TEXT_DISTANCE * 4 <= state.position[1] <= TEXT_DISTANCE * 4 + 50:
            state.run = False

    elif state.menu_placement == "controls_options":
        if event.button == 4:
            if state.scroll > 0:
                state.scroll -= 1
        elif event.button == 5:
            if state.scroll < len(state.controls) - SCREEN_SIZE[1] // TEXT_DISTANCE - 1:
                state.scroll += 1
        elif state.position[1] % TEXT_DISTANCE <= 50:
            state.control_adjusted = state.scroll + state.position[1] // TEXT_DISTANCE

    elif state.menu_placement == "credits":
        if state.position[1] <= 50:
            state.menu_placement = "main_menu"
    return chunks
