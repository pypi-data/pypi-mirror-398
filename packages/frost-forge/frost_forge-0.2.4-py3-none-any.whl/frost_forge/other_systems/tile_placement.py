from ..info import MULTI_TILES, RECIPES


def place_tile(kind, grid_position, chunks):
    if kind in MULTI_TILES:
        width, height = MULTI_TILES[kind]
        for x in range(width):
            for y in range(height):
                chunk_pos = (
                    grid_position[0][0] + (grid_position[1][0] + x) // 16,
                    grid_position[0][1] + (grid_position[1][1] + y) // 16,
                )
                tile_pos = (
                    (grid_position[1][0] + x) % 16,
                    (grid_position[1][1] + y) % 16,
                )
                tile_type = "left" if y == 0 else "up"
                if tile_pos not in chunks[chunk_pos]:
                    chunks[chunk_pos][tile_pos] = {"kind": tile_type}
                elif "floor" in chunks[chunk_pos][tile_pos]:
                    chunks[chunk_pos][tile_pos] = {
                        "kind": tile_type,
                        "floor": chunks[chunk_pos][tile_pos]["floor"],
                    }
    if (
        grid_position[1] in chunks[grid_position[0]]
        and "floor" in chunks[grid_position[0]][grid_position[1]]
    ):
        chunks[grid_position[0]][grid_position[1]] = {
            "kind": kind,
            "floor": chunks[grid_position[0]][grid_position[1]]["floor"],
        }
    else:
        chunks[grid_position[0]][grid_position[1]] = {"kind": kind}
    if kind in RECIPES:
        chunks[grid_position[0]][grid_position[1]]["recipe"] = -1
    return chunks
