from noise import pnoise2
from math import tan
from random import choice

from ..info import STRUCTURE_SIZE, ADJACENT_ROOMS, STRUCTURE_ROOMS


def structure_structure(dungeon_type, offset, dungeon=None, tile=None, distanse=1):
    if dungeon == None:
        dungeon = set()
    if tile == None:
        tile = offset
    dungeon.add(tile)
    for pos in ADJACENT_ROOMS:
        if (
            pnoise2(offset[0] + distanse ** 2, offset[1] + distanse ** 2, 3, 0.5, 2) + 0.5 < STRUCTURE_SIZE[dungeon_type] ** distanse
            and (tile[0] + pos[0], tile[1] + pos[1]) not in dungeon
        ):
            dungeon = structure_structure(
                dungeon_type,
                offset,
                dungeon,
                (tile[0] + pos[0], tile[1] + pos[1]),
                distanse + 1,
            )
    return dungeon


def add_hallways(hallways, room, adj_room):
    if isinstance(room, tuple) and isinstance(adj_room, tuple):
        hallways.setdefault(room, set()).add(adj_room)
        hallways.setdefault(adj_room, set()).add(room)
    return hallways


def structure_hallways(room, dungeon, hallways=None, visited=None):
    if hallways == None:
        hallways = {}
    if visited == None:
        visited = set()
    visited.add(room)
    for pos in ADJACENT_ROOMS:
        adj_room = (room[0] + pos[0], room[1] + pos[1])
        if adj_room in dungeon:
            if pnoise2(room[0] ** 3 + pos[0], room[1] ** 3 + pos[1], 3, 0.5, 2) < 0.5:
                hallways = add_hallways(hallways, room, adj_room)
                if adj_room not in visited:
                    hallways = structure_hallways(
                        (room[0] + pos[0], room[1] + pos[1]),
                        dungeon,
                        hallways,
                        visited=visited,
                    )
    return hallways


def ensure_hallways(dungeon, hallways, room, visited=None):
    if visited == None:
        visited = set()
    visited.add(room)
    adj_dungeon_rooms = []
    for pos in ADJACENT_ROOMS:
        adj_room = (room[0] + pos[0], room[1] + pos[1])
        if adj_room not in visited:
            if adj_room in hallways:
                hallways = add_hallways(hallways, room, adj_room)
                return hallways
            elif adj_room in dungeon:
                adj_dungeon_rooms.append(adj_room)
    if len(adj_dungeon_rooms):
        adj_noise_value = int((pnoise2(tan(room[0]), tan(room[1]), 3, 0.5, 2) + 0.5) * len(adj_dungeon_rooms))
        next_room = adj_dungeon_rooms[adj_noise_value]
        hallways = add_hallways(hallways, room, next_room)
        hallways = ensure_hallways(dungeon, hallways, next_room, visited)
    return hallways


def structure_rooms(dungeon_type, offset):
    structure = structure_structure(dungeon_type, offset)
    if len(structure) > 1:
        hallways = structure_hallways((0, 0), structure)
        for room in structure:
            if room not in hallways:
                hallways = ensure_hallways(structure, hallways, room)
    else:
        hallways = {}
    y = 0
    while (offset[0], y + offset[1]) in structure:
        y -= 1
    entrance = (offset[0], y + 1 + offset[1])
    dungeon = {}
    for room in structure:
        dungeon[room] = choice(STRUCTURE_ROOMS[dungeon_type])
    return dungeon, hallways, entrance
