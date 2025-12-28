from collections import deque

from ...other_systems.walk import walkable
from ...info import DIRECTION, MOVEMENT_TYPE


def bfs(start, goal, chunks, current_tile):
    blocked = set()
    for chunk in chunks:
        for tile in chunks[chunk]:
            if (
                not walkable(chunks, chunk, tile)
                and chunks[chunk][tile].get("kind") != "player"
                and chunks[chunk][tile].get("kind") != current_tile["kind"]
            ):
                blocked.add((chunk[0] * 16 + tile[0], chunk[1] * 16 + tile[1]))

    queue = deque([start])
    visited = {start: None}
    directions = DIRECTION[MOVEMENT_TYPE.get(current_tile["kind"], 0)]

    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)
            if (
                start[0] - 8 <= neighbor[0] < start[0] + 8
                and start[1] - 8 <= neighbor[1] < start[1] + 8
                and neighbor not in blocked
                and neighbor not in visited
            ):
                queue.append(neighbor)
                visited[neighbor] = current

    path = []
    if goal in visited:
        cur = goal
        while cur != start:
            path.append(cur)
            cur = visited[cur]
        path.reverse()
    return path
