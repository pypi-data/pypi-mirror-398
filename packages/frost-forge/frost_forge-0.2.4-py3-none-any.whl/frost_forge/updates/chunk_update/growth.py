from random import random

from ...info import GROW_TIME, GROW_TILES, GROW_REQUIREMENT, SOIL_STRENGTH, WORLD_ABILITIES, GROW_FLOOR_DELETE


def grow(tile, world_type, guarantee=False):
    if "kind" in tile:
        old_kind = tile["kind"]
    else:
        old_kind = tile["floor"]
    if random() < SOIL_STRENGTH.get(tile.get("floor"), 1) / (GROW_TIME[old_kind] * 6) or guarantee:
        if GROW_REQUIREMENT.get(old_kind, 1) <= SOIL_STRENGTH.get(tile.get("floor"), 1):
            for info in GROW_TILES[old_kind]:
                tile[info] = GROW_TILES[old_kind][info]
            if "inventory" in GROW_TILES[old_kind]:
                tile["inventory"] = {}
                for item in GROW_TILES[old_kind]["inventory"]:
                    if world_type not in WORLD_ABILITIES["saplingless"] or item.split(" ")[-1] != "sapling":
                        tile["inventory"][item] = GROW_TILES[old_kind]["inventory"][item]
    if tile.get("floor") in GROW_FLOOR_DELETE:
        del tile["floor"]
    return tile
