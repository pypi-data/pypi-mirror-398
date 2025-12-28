NOISE_STRUCTURES = {
    "forest": (((0, 0.01), "mushroom hut"),),
    "mountain": (((0, 0.01), "mineshaft"), ((0.11, 0.12), "amethyst geode")),
    "plains": (((0, 0.005), "copper dungeon"),),
}
ROOM_COLORS = {
    "amethyst geode": {
        (95, 81, 114): {"kind": "amethyst brick", "floor": "amethyst brick floor"},
        (123, 104, 150): {"floor": "amethyst brick floor"},
        (160, 138, 193): {"floor": "amethyst mineable"},
        (136, 68, 31): {"kind": "judge", "floor": "amethyst brick floor"},
    },
    "copper dungeon": {
        (136, 68, 31): {"kind": "copper brick", "floor": "copper brick floor"},
        (181, 102, 60): {"floor": "copper brick floor"},
        (228, 148, 106): {"floor": "copper door"},
        (138, 138, 140): {"kind": "skeleton", "floor": "copper brick floor"},
        (207, 206, 215): {"kind": "stone brick", "floor": "stone brick floor"},
        (247, 247, 255): {"floor": "stone brick floor"},
        (53, 53, 54): {"kind": "furnace", "loot": "copper furnace", "floor": "stone floor", "recipe": 1},
        (83, 107, 120): {"kind": "left", "floor": "stone floor"},
        (104, 130, 140): {"kind": "up", "floor": "stone floor"},
        (123, 104, 150): {"kind": "wooden table", "floor": "wood floor", "loot": "banquet table"},
        (73, 58, 37): {"kind": "small crate", "floor": "wood floor", "loot": "library shelf"},
        (92, 74, 49): {"kind": "bookshelf", "floor": "wood floor"},
        (60, 181, 71): {"kind": "small crate", "floor": "wood floor", "loot": "copper treasure"},
    },
    "mineshaft": {
        (53, 53, 54): {"kind": "stone brick", "floor": "stone floor"},
        (138, 138, 140): {"floor": "stone brick floor"},
        (247, 247, 255): {"kind": "rock", "floor": "stone floor"},
        (73, 58, 37): {"kind": "log", "floor": "wood floor"},
        (92, 74, 49): {"kind": "wood", "floor": "wood floor"},
        (129, 107, 63): {"floor": "wood door"},
        (19, 17, 18): {"kind": "coal ore", "inventory": {"coal": 1}, "floor": "stone floor"},
        (123, 104, 150): {"kind": "small crate", "loot": "mine chest", "floor": "stone floor"},
        (60, 181, 71): {"kind": "slime", "inventory": {"slime ball": 1}, "floor": "stone floor"},
    },
    "mushroom hut": {
        (247, 247, 255): {"kind": "mushroom block", "floor": "mushroom floor"},
        (138, 138, 140): {"floor": "mushroom floor"},
        (53, 53, 54): {"floor": "mushroom door"},
        (106, 228, 138): {"kind": "mushroom shaper", "floor": "mushroom floor"},
        (92, 74, 49): {"kind": "small crate", "loot": "mushroom chest", "floor": "mushroom floor"},
    },
}
STRUCTURE_ENTRANCE = {
    "amethyst geode": {"kind": "amethyst", "floor": "amethyst mineable"},
    "copper dungeon": {"kind": "glass lock", "floor": "copper door"},
    "mineshaft": {"floor": "stone floor"},
    "mushroom hut": {"floor": "mushroom door"},
}
STRUCTURE_SIZE = {"amethyst geode": 0, "copper dungeon": 0.6, "mushroom hut": 0.1, "mineshaft": 0.4}
STRUCTURE_ROOMS = {
    "amethyst geode": ("amethyst geode",),
    "copper dungeon": ("treasury", "hallway", "library", "banquet", "forge"),
    "mineshaft": ("hallway", "coal mine"),
    "mushroom hut": ("mushroom hut",),
}
STRUCTURE_HALLWAYS = {
    "copper dungeon": {"floor": "copper brick floor"},
    "mineshaft": {"floor": "stone brick floor"},
    "mushroom hut": {"floor": "mushroom floor"},
}
ADJACENT_ROOMS = ((0, -1), (0, 1), (-1, 0), (1, 0))
