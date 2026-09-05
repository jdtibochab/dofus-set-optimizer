
elements = [
    36, # Agility,
    22, # Chance
    13, # Intelligence
    45, # Strength
    9, # Vitality
    10, # Wisdom
]

# Base configuration for the optimizer and character
base_config = {
    "optimizer" : {
        "language": "es",
        "population_size": 300,
        "num_parents_mating": 100, # Number of parents to mate, usually 1/3 of population size
        "num_generations": 1000,
        "mutation_rate": 0.1,
        "crossover_rate": 0.8,
        "parent_selection_type": "tournament",  # Tournament Selection
        "tournament_size": 3,
        "exclusions": {
            "items": [6894,
                        6895,
                        3080,
                        9031,
                        6980, # Vulbis
                        13344, # Dolmanax
                        32121, # Bota	Clarividencia de Mériana	200	32121
                        ]  # Excluded items
        },
        "inclusions": {
            "items": [
                # 14093, # Botas kuko
                # 18718, # Escudo kuko
                # 14092, # Anillo kuko
                # 8993, # Espada maldita
                7754, # Dofus ocre
            ]
        },
        "preferences": {
            "lower": {
                12: {
                    "target": 12,  # AP
                    "strength": 0.1,  # Penalty for not meeting the target
                },
                8: {
                    "target": 6,  # MP
                    "strength": 0.1,  # Penalty for not meeting the target
                },
                # 29: {
                #     "target": 80,  # Crit
                #     "strength": 0.75,  # Penalty for not meeting the target
                # },
                9: {
                    "target": 4000,  # Vit
                    "strength": 0.1,  # Penalty for not meeting the target
                },
                34 : {
                    "target": 15, # %res neutral
                    "strength": 0.1,  # Penalty for not meeting the target
                },
                37 : {
                    "target": 15, # %res fire
                    "strength": 0.1,  # Penalty for not meeting the target
                },
                16 : {
                    "target": 15, # %res air
                    "strength": 0.1,  # Penalty for not meeting the target
                },
                17 : {
                    "target": 15, # %res water
                    "strength": 0.1,  # Penalty for not meeting the target
                },
                63 : {
                    "target": 15, # %res range
                    "strength": 0.1,  # Penalty for not meeting the target
                }
            },
            "upper": {}
        },

        "level_offset": 10,  # Level offset for items
        "objective": "weapon",  # Objective to optimize, can be "weapon" or "elements"
        "normalize_by_apcost" : False # If False, only care about absolute damage regardless of AP cost
    },
    "character": {
        "level": 200,
        "scrolled": True,
        "exo": {
        #     12:1, # Exo AP
        #     8:1 # Exo MP
            },
        "distributed_points": {
        #     9: 595,  # Vitality
        },
        "elements" : [
        #     36, # Agility,
        #     22, # Chance
        #     13, # Intelligence
        #     45  # Strength
        ],
        "melee" : True,
        "ranged" : True
    }
}

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

def get_set_contribution(item_set, overlap):
    set_effects = item_set["effects"]
    contributions = {}
    if set_effects is not None:
        for d in set_effects.get(str(overlap), []):
            field = "max" if d["min_max_irrelevant"] == 0 else "min"
            contributions[d["element_id"]] = d[field]
    # Add to set bonus
    contributions[72] = overlap - 1
    return contributions

def get_item_set(item, item_sets):
    if not item.get("hasParentSet", False):
        return None
    return item_sets[item["parentSet"]["id"]]
