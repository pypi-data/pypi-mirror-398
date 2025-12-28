from noise import pnoise2

from ..info import BIOMES, WORLD_ABILITIES


def determine_biome(world_type, world_x, world_y, noise_offset):
    if world_type in WORLD_ABILITIES["large biomes"]:
        biome_value = pnoise2(
            world_x / 600 + noise_offset[0], world_y / 600 + noise_offset[1], 3, 0.5, 2
        )
    else:
        biome_value = pnoise2(
            world_x / 240 + noise_offset[0], world_y / 240 + noise_offset[1], 3, 0.5, 2
        )
    biome = "plains"
    for noise_chunk in BIOMES:
        if noise_chunk[0] < biome_value < noise_chunk[1]:
            biome = noise_chunk[2]
            break
    return biome
