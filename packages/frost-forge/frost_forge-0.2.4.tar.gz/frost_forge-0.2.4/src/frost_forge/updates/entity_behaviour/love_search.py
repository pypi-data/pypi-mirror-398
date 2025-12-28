def search_love(chunks, chunk, tile, search_list):
    for x, y in search_list:
        check_chunk = (chunk[0] + (tile[0] + x) // 16, chunk[1] + (tile[1] + y) // 16)
        check_tile = ((tile[0] + x) % 16, (tile[1] + y) % 16)
        if check_tile in chunks[check_chunk] and "kind" in chunks[check_chunk][check_tile]:
            if chunks[check_chunk][check_tile]["kind"] == chunks[chunk][tile]["kind"] and "love" in chunks[check_chunk][check_tile]:
                return True, check_chunk, check_tile
    return False, 0, 0
