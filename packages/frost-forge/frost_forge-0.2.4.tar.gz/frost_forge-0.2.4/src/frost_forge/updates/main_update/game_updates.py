import pygame as pg

from ..input_update.player_move import move_player
from ...world_generation.world_generation import generate_chunk
from ...world_generation.structure_generation import generate_structure
from ...other_systems.game_saving import save_game
from ...other_systems.walk import walkable
from ..input_update.mouse_update import button_press
from ...info import DAY_LENGTH, RECIPES, ACHIEVEMENTS, FPS, FLOOR_TYPE, WORLD_ABILITIES, FLOOR_DAMAGE


def update_game(state, chunks):
    state.location["old"] = list(state.location["tile"])
    key = pg.key.get_pressed()
    state.location, state.velocity = move_player(
        key, state.controls, state.velocity, state.location, state.accessory
    )

    for x in range(-4, 5):
        for y in range(-4, 5):
            generate_chunk(
                state.world_type,
                state.location["tile"][0] + x,
                state.location["tile"][1] + y,
                chunks,
                state.noise_offset,
            )
    if state.world_type in WORLD_ABILITIES["structures"]:
        for x in range(-10, 11):
            for y in range(-10, 11):
                chunks, state.checked, state.save_chunks = generate_structure(
                    state.world_type,
                    state.noise_offset,
                    state.location["tile"][0] + x,
                    state.location["tile"][1] + y,
                    chunks,
                    state.checked,
                    state.save_chunks,
                )

    tile_chunk_coords = (state.location["tile"][0], state.location["tile"][1])
    tile_coords = (state.location["tile"][2], state.location["tile"][3])
    old_chunk_coords = (state.location["old"][0], state.location["old"][1])
    old_tile_coords = (state.location["old"][2], state.location["old"][3])

    chunk = chunks[tile_chunk_coords]
    old_chunk = chunks[old_chunk_coords]
    old_tile = old_chunk[old_tile_coords]

    if state.health <= 0:
        if "floor" in chunk[tile_coords]:
            chunk[tile_coords] = {
                "kind": "corpse",
                "inventory": state.inventory,
                "floor": chunk[tile_coords]["floor"],
            }
        else:
            chunk[tile_coords] = {"kind": "corpse", "inventory": state.inventory}
        chunks[0, 0][0, 2] = {"kind": "player", "floor": "void", "recipe": 0}
        state.health = state.max_health
        state.inventory = {}
        state.location["real"] = [0, 0, 0, 2]
        state.location["tile"] = [0, 0, 0, 2]

    else:
        if tile_coords not in chunk:
            chunk[tile_coords] = {"kind": "player", "recipe": old_tile["recipe"]}
        elif walkable(chunks, tile_chunk_coords, tile_coords):
            chunk[tile_coords]["kind"] = "player"
            chunk[tile_coords]["recipe"] = old_tile["recipe"]
        elif FLOOR_TYPE.get(chunk[tile_coords].get("floor", None), None) == "fluid":
            chunk[tile_coords]["kind"] = "player submerged"
            chunk[tile_coords]["recipe"] = old_tile["recipe"]
        elif chunk[tile_coords].get("kind") != "player":
            state.location["real"] = list(state.location["old"])
            state.location["real"][2] += 0.5
            state.location["real"][3] += 0.5
            state.location["tile"] = list(state.location["old"])
            state.velocity = [0, 0]

        if state.location["old"] != state.location["tile"]:
            if "floor" in old_tile:
                del old_chunk[old_tile_coords]["kind"]
                del old_chunk[old_tile_coords]["recipe"]
            else:
                del old_chunk[old_tile_coords]

    if state.location["opened"] == (
        (state.location["old"][0], state.location["old"][1]),
        (state.location["old"][2], state.location["old"][3]),
    ):
        state.location["opened"] = (
            (state.location["tile"][0], state.location["tile"][1]),
            (state.location["tile"][2], state.location["tile"][3]),
        )
    
    if chunks[state.location["tile"][0], state.location["tile"][1]][state.location["tile"][2], state.location["tile"][3]].get("floor", None) in FLOOR_DAMAGE and state.tick % FPS == 0:
        state.health -= FLOOR_DAMAGE[chunks[state.location["tile"][0], state.location["tile"][1]][state.location["tile"][2], state.location["tile"][3]]["floor"]]

    for event in pg.event.get():
        if event.type == pg.QUIT:
            state.run = False
        elif event.type == pg.MOUSEBUTTONDOWN:
            (
                chunks,
                state.location,
                state.machine_ui,
                state.machine_inventory,
                state.tick,
                state.inventory_number,
                state.health,
                state.max_health,
                state.inventory,
                recipe_number,
                state.accessory,
            ) = button_press(
                event.button,
                state.position,
                state.zoom,
                chunks,
                state.location,
                state.machine_ui,
                state.inventory,
                state.health,
                state.max_health,
                state.machine_inventory,
                state.tick,
                state.inventory_number,
                chunks[state.location["opened"][0]][state.location["opened"][1]].get("recipe", -1),
                state.camera,
                state.inventory_size,
                state.world_type,
                state.accessory,
            )
            if "recipe" in chunks[state.location["opened"][0]][state.location["opened"][1]]:
                chunks[state.location["opened"][0]][state.location["opened"][1]]["recipe"] = recipe_number
        elif event.type == pg.KEYDOWN:
            keys = pg.key.get_pressed()
            if keys[state.controls[4]]:
                if state.machine_ui == "game":
                    state.machine_ui = "player"
                    state.location["opened"] = (
                        (state.location["tile"][0], state.location["tile"][1]),
                        (state.location["tile"][2], state.location["tile"][3]),
                    )
                else:
                    state.machine_ui = "game"
                    state.location["opened"] = ((0, 0), (0, 0))
            elif keys[state.controls[5]] or keys[state.controls[6]]:
                state.target_zoom += (
                    keys[state.controls[5]] - keys[state.controls[6]]
                ) / 4
                state.target_zoom = min(max(state.target_zoom, 0.5), 2)
            elif keys[state.controls[21]]:
                if state.machine_ui not in RECIPES:
                    state.menu_placement = "options_game"
                else:
                    chunks[state.location["opened"][0]][state.location["opened"][1]]["recipe"] = -1
            elif keys[state.controls[19]] or keys[state.controls[20]]:
                if state.machine_ui not in RECIPES:
                    state.inventory_number = (state.inventory_number + keys[state.controls[19]] - keys[state.controls[20]]) % state.inventory_size[0]
                else:
                    recipe_number = chunks[state.location["opened"][0]][state.location["opened"][1]]["recipe"]
                    recipe_number = (recipe_number + keys[state.controls[19]] - keys[state.controls[20]]) % len(RECIPES[state.machine_ui])
                    chunks[state.location["opened"][0]][state.location["opened"][1]]["recipe"] = recipe_number
            for i in range(7, 19):
                if keys[state.controls[i]]:
                    state.inventory_number = i - 7

    for achievement in ACHIEVEMENTS:
        if achievement in state.inventory and achievement not in state.achievements:
            state.achievements.add(achievement)
            state.achievement_popup = [10 * FPS, achievement]

    state.tick += 1
    state.achievement_popup[0] = max(state.achievement_popup[0] - 1, 0)
    state.save_chunks.add((state.location["tile"][0], state.location["tile"][1]))
    if state.tick % (DAY_LENGTH // 4) == 0:
        save_game(chunks, state, f"autosave_{(state.tick // (DAY_LENGTH // 4)) % 4}")
    state.zoom = 0.05 * state.target_zoom + 0.95 * state.zoom
    return chunks
