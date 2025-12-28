from .tile_rendering import render_tile


def render_map(location, chunks, camera, zoom, scaled_image, window, images):
    for chunk_y in range(-2, 3):
        for chunk_x in range(-2, 3):
            chunk = (chunk_x + location["tile"][0], chunk_y + location["tile"][1])
            if chunk in chunks:
                for y in range(0, 16):
                    for x in range(0, 16):
                        tile = (x, y)
                        if tile in chunks[chunk]:
                            render_tile(
                                chunk,
                                tile,
                                zoom,
                                camera,
                                scaled_image,
                                chunks,
                                window,
                                images,
                            )
    return window
