from .entity_movement import move_entity
from ...info import DAMAGE, RANGE


def enemy(
    chunks, chunk, tile, current_tile, location, health, player_distance, create_tile
):
    if player_distance <= RANGE.get(chunks[chunk][tile]["kind"], 1):
        health -= DAMAGE.get(chunks[chunk][tile]["kind"], 1)
    elif player_distance < 73:
        chunks, create_tile = move_entity(chunks, chunk, tile, current_tile, 1, location, create_tile)
    else:
        chunks, create_tile = move_entity(chunks, chunk, tile, current_tile, 0, location, create_tile)
    return chunks, health, create_tile
