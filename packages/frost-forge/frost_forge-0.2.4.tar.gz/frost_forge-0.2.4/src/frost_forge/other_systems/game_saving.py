from os import path

from ..info import SAVES_FOLDER


def save_game(chunks, state, file):
    chunks_saved = {}
    for chunk in state.save_chunks:
        chunks_saved[chunk] = chunks[chunk]
    with open(path.join(SAVES_FOLDER, f"{file}.txt"), "w", encoding="utf-8") as file:
        file.write(
            f"{chunks_saved};{state.location['tile']};{state.inventory};{state.max_health};{state.tick};{state.noise_offset};{state.world_type};{state.checked};{state.save_chunks};{state.achievements};{state.inventory_size};{state.accessory}"
        )
