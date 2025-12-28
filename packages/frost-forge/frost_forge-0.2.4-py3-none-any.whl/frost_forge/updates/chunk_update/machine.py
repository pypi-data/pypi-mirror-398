from math import sqrt, log2

from ..left_click import recipe
from ...info import RUNES_USER, RUNES, RECIPES, PROCESSING_TIME


def machine(tick, current_tile, kind, attributes, tile, chunk, chunks):
    if "inventory" not in current_tile:
        machine_inventory = {}
    else:
        machine_inventory = current_tile["inventory"]
    if tick % PROCESSING_TIME[kind] == 0 and current_tile.get("recipe", -1) >= 0:
        if "drill" in attributes and "floor" in current_tile:
            if current_tile["floor"].split(" ")[-1] == "mineable":
                machine_inventory[current_tile["floor"]] = 1
        craftable = True
        if kind in RUNES_USER:
            mana = 0
            for x in range(-RUNES_USER[kind], RUNES_USER[kind] + 1):
                for y in range(-RUNES_USER[kind], RUNES_USER[kind] + 1):
                    if sqrt(x ** 2 + y ** 2) <= RUNES_USER[kind]:
                        rune_tile = ((tile[0] + x) % 16, (tile[1] + y) % 16)
                        rune_chunk = (chunk[0] + (tile[0] + x) // 16, chunk[1] + (tile[1] + y) // 16)
                        if rune_tile in chunks[rune_chunk] and "floor" in chunks[rune_chunk][rune_tile]:
                            rune = chunks[rune_chunk][rune_tile]["floor"]
                            if rune in RUNES:
                                if RUNES[rune][0] == 0:
                                    mana += RUNES[rune][1]
                                elif RUNES[rune][0] == 1:
                                    mana *= RUNES[rune][1]
                                    mana += RUNES[rune][2]
            if int(log2(mana ** 1.2 + 2)) != RECIPES[kind][current_tile["recipe"]][2]:
                craftable = False
            machine_inventory["mana_level"] = int(log2(mana ** 1.2 + 2))
        if craftable:
            machine_inventory = recipe(kind, current_tile["recipe"], machine_inventory, (20, 64))
    return machine_inventory