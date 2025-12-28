from ..info import MULTI_TILES, FLOOR_TYPE, GROW_TILES, GROW_DIRT_IGNORE


def is_placable(kind, grid_position, chunks):
    tile_size = MULTI_TILES.get(kind, (1, 1))
    for x in range(0, tile_size[0]):
        for y in range(0, tile_size[1]):
            tile_coord = (
                int((grid_position[1][0] + x) % 16),
                int((grid_position[1][1] + y) % 16),
            )
            chunk_coord = (
                grid_position[0][0] + (grid_position[1][0] + x) // 16,
                grid_position[0][1] + (grid_position[1][1] + y) // 16,
            )
            if tile_coord in chunks[chunk_coord]:
                current_tile = chunks[chunk_coord][tile_coord]
                if "kind" in current_tile:
                    return False
                elif "floor" in current_tile:
                    tile_floor_type = FLOOR_TYPE.get(current_tile["floor"])
                    if tile_floor_type in {"block", "fluid", "tile"}:
                        return False
                    elif kind in GROW_TILES and kind not in GROW_DIRT_IGNORE and current_tile["floor"].split()[-1] != "dirt":
                        return False
            elif kind in GROW_TILES and kind not in GROW_DIRT_IGNORE:
                return False
    return True
