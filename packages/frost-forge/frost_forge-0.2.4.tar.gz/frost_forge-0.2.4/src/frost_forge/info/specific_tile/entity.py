ATTRACTION = {
    "furless rabbit": "carrot",
    "rabbit adult": "carrot",
    "rabbit child": "carrot",
}
BREEDABLE = {
    "rabbit adult": {"kind": "rabbit child"}
}
DAMAGE = {
    "quartz adult": 0,
    "quartz child": 0,
    "slime prince": 2,
}
MOVEMENT_TYPE = {
    "slime prince": 1
}
RANGE = {
    "slime prince": 4,
}
DIRECTION = (
    ((1, 0), (-1, 0), (0, 1), (0, -1)),
    ((1, 0), (-1, 0), (0, 1), (0, -1), (-1, -1), (-1, 1), (1, -1), (1, 1), (2, 0), (-2, 0), (0, -2), (0, 2))
)