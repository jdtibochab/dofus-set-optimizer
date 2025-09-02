
elements = [
    36, # Agility,
    22, # Chance
    13, # Intelligence
    45, # Strength
    9, # Vitality
    10, # Wisdom
]

damage_mapper = {
        # Damage
            189 : 36, # Air,
            214 : 22, # Water
            198 : 13, # Fire
            194 : 45, # Earth
            195 : 45, # Neutral (by earth)
        # Steal
            224 : 36, # Air,
            203 : 22, # Water
            193 : 13, # Fire
            221 : 45, # Earth
            223 : 45, # Neutral
        }
bonus_damage_mapper = {
        # Damage
            189 : 47, # Air,
            214 : 27, # Water
            198 : 61, # Fire
            194 : 48, # Earth
            195 : 49, # Neutral
        # Steal
            224 : 47, # Air,
            203 : 27, # Water
            193 : 61, # Fire
            221 : 48, # Earth
            223 : 49, # Neutral
    }

default_soft_caps = {
    9: [0,None, 0, 0, 0, 0], # Vitality
    10: [0, 0, 0, None, 0, 0], # Wisdom
    45: [0, 100, 200, 300, None, 0], # Strength
    13: [0, 100, 200, 300, None, 0], # Intelligence
    22: [0, 100, 200, 300, None, 0], # Chance
    36: [0, 100, 200, 300, None, 0]  # Agility
}

def get_item_contribution(item):
    # Get the effects of the item
    item_effects = item["effects"]
    if not item_effects:
        return {}
    contributions = {}
    for d in item_effects:
        field = "max" if d["min_max_irrelevant"] == 0 else "min"
        contributions[d["element_id"]] = d[field]
    if item["type"]["superTypeId"] == 27: # Weapon
        contributions[212] = 1
    return contributions

def get_set_contribution(item_set,overlap):
    set_effects = item_set["effects"][str(overlap)]
    contributions = {}
    for d in set_effects:
        field = "max" if d["min_max_irrelevant"] == 0 else "min"
        contributions[d["element_id"]] = d[field]
    # Add to set bonus
    contributions[72] = overlap - 1
    return contributions

def get_item_set(item, item_sets):
    if not item.get("hasParentSet", False):
        return None
    return item_sets[item["parentSet"]["id"]]
