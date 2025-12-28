from ...world_generation.world_generation import generate_chunk
from ...info import WORLD_ABILITIES


def save_creating(state, chunks):
    state.save_file_name = ""
    state.menu_placement = "main_game"
    chunks = {}
    state.save_chunks = {(0, 0)}
    state.checked = set()
    state.achievements = set()
    state.location["tile"] = [0, 0, 0, 2]
    state.location["real"] = [0, 0, 0, 2]
    state.noise_offset = generate_chunk(state.world_type, 0, 0, chunks, seed=state.seed)
    for x in range(-4, 5):
        for y in range(-4, 5):
            generate_chunk(
                state.world_type,
                state.location["tile"][0] + x,
                state.location["tile"][1] + y,
                chunks,
                state.noise_offset,
            )
    if state.world_type in WORLD_ABILITIES["skyblock"]:
        chunks[0, 0][0, 0] = {"kind": "void crate", "inventory": {"flint axe": 1, "sapling": 1, "dirt": 1, "composter": 1}}
        chunks[0, 0][0, 1] = {"kind": "void converter"}
    else:
        chunks[0, 0][0, 0] = {"kind": "obelisk"}
        chunks[0, 0][0, 1] = {"kind": "up"}
    chunks[0, 0][0, 2] = {"kind": "player", "floor": "void", "recipe": -1}
    state.tick = 0
    state.inventory = {}
    state.max_health = 20
    state.health = 20
    state.inventory_size = [12, 64]
    state.accessory = []
    return chunks
