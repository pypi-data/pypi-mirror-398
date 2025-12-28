from .entity_movement import move_entity
from .empty_place import find_empty_place
from .love_search import search_love
from ...info import ATTRACTION, ADJACENT_ROOMS, BREEDABLE


def animal(
    chunks,
    chunk,
    tile,
    current_tile,
    location,
    inventory_key,
    player_distance,
    create_tile,
):
    move = True
    if "love" in current_tile:
        found_love, love_chunk, love_tile = search_love(chunks, chunk, tile, ADJACENT_ROOMS)
        if found_love:
            empty = find_empty_place(tile, chunk, chunks)
            if empty:
                if empty[1] not in chunks[empty[0]]:
                    chunks[empty[0]][empty[1]] = {}
                for info in BREEDABLE[current_tile["kind"]]:
                    chunks[empty[0]][empty[1]][info] = BREEDABLE[current_tile["kind"]][info]
                chunks[chunk][tile]["love"] = 0
        else:
            found_love, love_chunk, love_tile = search_love(chunks, chunk, tile, ((x, y) for x in range(-4, 5) for y in range(-4, 5)))
            if found_love:
                chunks, create_tile = move_entity(chunks, chunk, tile, current_tile, 1, (*love_chunk, *love_tile), create_tile)
                move = False
        chunks[chunk][tile]["love"] -= 1
        if chunks[chunk][tile]["love"] <= 0:
            del chunks[chunk][tile]["love"]
    if move:
        if player_distance < 73 and inventory_key == ATTRACTION[current_tile["kind"]]:
            chunks, create_tile = move_entity(chunks, chunk, tile, current_tile, 1, location, create_tile)
        else:
            chunks, create_tile = move_entity(chunks, chunk, tile, current_tile, 0, location, create_tile)
    return chunks, create_tile
