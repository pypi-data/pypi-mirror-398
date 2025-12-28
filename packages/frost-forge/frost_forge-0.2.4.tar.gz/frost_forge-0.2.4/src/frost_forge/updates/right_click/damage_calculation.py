from ...info import RESISTANCE, TOOL_EFFICIENCY, TOOL_REQUIRED, TOOLS


def calculate_damage(mining_type, inventory, inventory_number):
    damage = 1 - RESISTANCE.get(mining_type, 0)
    if len(inventory) > inventory_number:
        inventory_words = list(inventory.keys())[inventory_number].split()
        if len(inventory_words) == 2:
            if (
                mining_type in TOOL_REQUIRED
                and TOOL_REQUIRED[mining_type] == inventory_words[1]
            ):
                damage += TOOL_EFFICIENCY[inventory_words[0]]
            elif inventory_words[1] in TOOLS:
                return 0
    return max(damage, 0)
