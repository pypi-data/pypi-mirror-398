from ast import literal_eval
import os

from ...info import SAVES_FOLDER, TEXT_DISTANCE
from ...world_generation.world_generation import generate_chunk


def save_loading(state, chunks):
    saves = [f[:-4] for f in os.listdir(SAVES_FOLDER) if f.endswith(".txt")]
    index = (state.position[1] // TEXT_DISTANCE) - 2
    if index < len(saves):
        state.save_file_name = saves[index]
        if state.position[0] >= 120:
            state.menu_placement = "main_game"
            with open(
                os.path.join(SAVES_FOLDER, state.save_file_name + ".txt"),
                "r",
                encoding="utf-8",
            ) as file:
                file_content = file.read().split(";")
            chunks = literal_eval(file_content[0])
            state.location["tile"] = literal_eval(file_content[1])
            state.location["real"] = list(state.location["tile"])
            state.inventory = literal_eval(file_content[2])
            state.max_health = int(float(file_content[3]))
            state.health = state.max_health
            state.tick = int(float(file_content[4]))
            state.noise_offset = literal_eval(file_content[5])
            state.world_type = int(file_content[6])
            state.checked = literal_eval(file_content[7])
            state.save_chunks = literal_eval(file_content[8])
            state.achievements = literal_eval(file_content[9])
            state.inventory_size = literal_eval(file_content[10])
            state.accessory = literal_eval(file_content[11])
            for x in range(-4, 5):
                for y in range(-4, 5):
                    generate_chunk(
                        state.world_type,
                        state.location["tile"][0] + x,
                        state.location["tile"][1] + y,
                        chunks,
                        state.noise_offset,
                    )
        elif state.position[0] <= 90:
            file = os.path.join(SAVES_FOLDER, state.save_file_name + ".txt")
            if os.path.exists(file):
                os.remove(file)
    return chunks
