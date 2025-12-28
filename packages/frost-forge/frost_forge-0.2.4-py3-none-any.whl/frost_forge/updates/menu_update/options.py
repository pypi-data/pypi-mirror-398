from ...other_systems.game_saving import save_game
from ...info import TEXT_DISTANCE


def option(state, chunks):
    if state.menu_placement == "options_game":
        if 0 <= state.position[1] <= 50:
            state.menu_placement = "main_game"
        elif TEXT_DISTANCE * 2 <= state.position[1] <= TEXT_DISTANCE * 2 + 50:
            if (
                state.save_file_name != ""
                and state.save_file_name.split("_")[0] != "autosave"
            ):
                state.menu_placement = "main_menu"
                save_game(chunks, state, state.save_file_name)
                state.save_file_name = ""
                state.machine_ui = "game"
            else:
                state.menu_placement = "save_creation"
    elif state.menu_placement == "options_main":
        if 0 <= state.position[1] <= 50:
            state.menu_placement = "main_menu"
    if TEXT_DISTANCE <= state.position[1] <= TEXT_DISTANCE + 50:
        state.control_adjusted = -1
        state.menu_placement = "controls_options"
