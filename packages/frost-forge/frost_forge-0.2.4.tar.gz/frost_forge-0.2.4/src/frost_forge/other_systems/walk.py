from ..info import FLOOR_TYPE


def walkable(chunks, chunk, tile):
    if tile not in chunks[chunk]:
        return True
    elif "kind" in chunks[chunk][tile]:
        return False
    elif chunks[chunk][tile]["floor"].split()[-1] == "door":
        return False
    elif FLOOR_TYPE.get(chunks[chunk][tile]["floor"]) in {"fluid", "tile"}:
        return False
    return True
