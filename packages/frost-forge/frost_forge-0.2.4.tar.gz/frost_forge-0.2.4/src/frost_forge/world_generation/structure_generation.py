from noise import pnoise2

from ..info import NOISE_STRUCTURES, STRUCTURE_ENTRANCE, STRUCTURE_HALLWAYS
from .room_generation import generate_room
from .structure_structuring import structure_rooms
from .biome_determination import determine_biome


def generate_structure(world_type, noise_offset, chunk_x, chunk_y, chunks, checked, save_chunks):
    if (chunk_x, chunk_y) not in checked:
        checked.add((chunk_x, chunk_y))
        structure_value = pnoise2(
            chunk_x + noise_offset[0], chunk_y + noise_offset[1], 3, 0.5, 2
        )
        structure = False
        biome = determine_biome(
            world_type,
            16 * chunk_x + noise_offset[0],
            16 * chunk_y + noise_offset[1],
            noise_offset,
        )
        for noise_structure in NOISE_STRUCTURES.get(biome, ()):
            if noise_structure[0][0] < structure_value < noise_structure[0][1]:
                structure_type = noise_structure[1]
                structure = True
                break
        if structure:
            dungeon, hallways, entrance = structure_rooms(structure_type, (chunk_x, chunk_y))
            for dungeon_room in dungeon:
                if max(abs(dungeon_room[0]), abs(dungeon_room[1])) >= 2:
                    chunks[dungeon_room] = generate_room(
                        structure_type,
                        dungeon[dungeon_room],
                        dungeon_room,
                        dungeon[dungeon_room][0] == dungeon[dungeon_room][1],
                    )
                    save_chunks.add(dungeon_room)
                checked.add(dungeon_room)
            for room in hallways:
                for adjacent_room in hallways[room]:
                    if max(abs(room[0]), abs(room[1]), abs(adjacent_room[0]), abs(adjacent_room[1])) >= 2:
                        if room[0] != adjacent_room[0]:
                            if room[0] > adjacent_room[0]:
                                added_locations = ((0, 7), (0, 8))
                            else:
                                added_locations = ((15, 7), (15, 8))
                        else:
                            if room[1] > adjacent_room[1]:
                                added_locations = ((7, 0), (8, 0))
                            else:
                                added_locations = ((7, 15), (8, 15))
                        for location in added_locations:
                            chunks[room][location] = {}
                            for info in STRUCTURE_HALLWAYS[structure_type]:
                                chunks[room][location][info] = STRUCTURE_HALLWAYS[structure_type][info]
            if max(abs(entrance[0]), abs(entrance[1])) >= 2:
                chunks[entrance][7, 0] = STRUCTURE_ENTRANCE[structure_type]
    return chunks, checked, save_chunks
