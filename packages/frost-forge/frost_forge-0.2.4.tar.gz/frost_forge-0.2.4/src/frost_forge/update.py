from .other_systems.game_state import GameState
from .updates.main_update import update_menu, update_game, update_tiles
from .info import FPS


def update(state: GameState, chunks):
    if state.menu_placement != "main_game":
        chunks = update_menu(state, chunks)
    else:
        if state.tick % (FPS // 6) == 0:
            chunks = update_tiles(state, chunks)
        chunks = update_game(state, chunks)
    return chunks
