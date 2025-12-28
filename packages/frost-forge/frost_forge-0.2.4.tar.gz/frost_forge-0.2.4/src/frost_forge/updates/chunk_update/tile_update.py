from math import log2, sqrt

from .point import left, up
from ..entity_behaviour.animal import animal
from ..entity_behaviour.enemy import enemy
from .growth import grow
from .machine import machine
from ...info import ATTRIBUTES, GROW_TILES


def update_tile(
    current_tile,
    chunks,
    chunk,
    tile,
    tick,
    location,
    inventory_key,
    health,
    create_tile,
    world_type,
):
    kind = current_tile["kind"]
    attributes = ATTRIBUTES.get(kind, ())
    if kind == "left":
        chunks = left(chunks, chunk, tile)
    elif kind == "up":
        chunks = up(chunks, chunk, tile)
    elif "machine" in attributes:
        chunks[chunk][tile]["inventory"] = machine(tick, current_tile, kind, attributes, tile, chunk, chunks)
    elif kind in GROW_TILES:
        chunks[chunk][tile] = grow(current_tile, world_type)
        if chunks[chunk][tile] == {}:
            del chunks[chunk][tile]
    if "creature" in attributes:
        player_distance_x = abs(chunk[0] * 16 + tile[0] - location[0] * 16 - location[2])
        player_distance_y = abs(chunk[1] * 16 + tile[1] - location[1] * 16 - location[3])
        player_distance = player_distance_x ** 2 + player_distance_y ** 2
        if "animal" in attributes:
            chunks, create_tile = animal(
                chunks,
                chunk,
                tile,
                current_tile,
                location,
                inventory_key,
                player_distance,
                create_tile,
            )
        elif "enemy" in attributes:
            chunks, health, create_tile = enemy(
                chunks,
                chunk,
                tile,
                current_tile,
                location,
                health,
                player_distance,
                create_tile,
            )
    return chunks, health, create_tile
