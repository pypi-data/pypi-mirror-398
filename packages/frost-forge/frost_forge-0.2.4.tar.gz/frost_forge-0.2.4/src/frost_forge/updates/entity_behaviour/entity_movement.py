from random import randint

from .maze_solving import bfs
from ...other_systems.walk import walkable


def move_entity(
    chunks, chunk, tile, current_tile, type, location, create_tile,
):
    obscured_path = False
    if "goal" not in current_tile:
        if type == 0:
            goal = (randint(-8, 8), randint(-8, 8))
            current_tile["goal"] = (
                (
                    chunk[0] + int((tile[0] + goal[0]) / 16),
                    chunk[1] + int((tile[1] + goal[1]) / 16),
                ),
                ((tile[0] + goal[0]) % 16, (tile[1] + goal[1]) % 16),
            )
        elif type == 1:
            current_tile["goal"] = (
                (location[0], location[1]),
                (location[2], location[3]),
            )
        current_tile["path"] = []
        start = (chunk[0] * 16 + tile[0], chunk[1] * 16 + tile[1])
        goal = (
            current_tile["goal"][0][0] * 16 + current_tile["goal"][1][0],
            current_tile["goal"][0][1] * 16 + current_tile["goal"][1][1],
        )
        path = bfs(start, goal, chunks, current_tile)
        for road in path:
            current_tile["path"].append(
                ((road[0] // 16, road[1] // 16), (road[0] % 16, road[1] % 16))
            )
    if len(current_tile["path"]) > 0:
        path_chunk = current_tile["path"][0][0]
        path_tile = current_tile["path"][0][1]
        if walkable(chunks, path_chunk, path_tile):
            if path_tile not in chunks[path_chunk]:
                chunks[path_chunk][path_tile] = {}
            for info in current_tile:
                if info != "floor":
                    chunks[path_chunk][path_tile][info] = current_tile[info]
            current_tile["path"].pop(0)
            if "floor" in current_tile:
                chunks[chunk][tile] = {"floor": current_tile["floor"]}
            else:
                del chunks[chunk][tile]
            create_tile.add((path_chunk, path_tile))
        else:
            obscured_path = True
    if len(current_tile["path"]) == 0 or obscured_path:
        del current_tile["path"]
        del current_tile["goal"]
    return chunks, create_tile
