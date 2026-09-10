
import argparse
from datetime import datetime


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

def parse_args(configure_parser=None):
    """
    Build the command-line parser for the training workflow.

    Args:
        configure_parser (Any): Input value.

    Example:
        >>> parse_args(configure_parser=...)
    """
    parser = argparse.ArgumentParser(description="Run MLP embedding demo with different DBTL cycle splits")

    # Optimizer
    parser.add_argument('--normalize-by-apcost', action='store_true', help='Whether to normalize damage by AP cost', default=False)
    parser.add_argument('--objective', type=str, help='Objective to optimize, can be "weapon" or "elements"', default="weapon")

    parser.add_argument('--reference', type=str, nargs='+', help='Reference items', default=[])
    parser.add_argument('--population-size', type=int, help='Population size for the optimizer', default=100)
    parser.add_argument('--num-parents-mating', type=int, help='Number of parents to mate', default=100)
    parser.add_argument('--num-generations', type=int, help='Number of generations', default=200)
    parser.add_argument('--mutation-rate', type=float, help='Mutation rate', default=0.05)
    parser.add_argument('--crossover-rate', type=float, help='Crossover rate', default=0.8)
    parser.add_argument('--tournament-size', type=int, help='Tournament size for selection', default=3)
    parser.add_argument('--penalty-strength', type=float, help='Penalty for strength', default=0.1)


    # Items and characteristics
    parser.add_argument('--exclusions', type=int, nargs='+', help='Items to exclude', default=[])
    parser.add_argument('--inclusions', type=int, nargs='+', help='Items to include', default=[])
    parser.add_argument('--elements', type=int, nargs='+', help='Character elements', default=[
        36, # Agility,
        22, # Chance
        13, # Intelligence
        45  # Strength
    ])
    parser.add_argument('--melee', action='store_true', help='Whether the character is melee', default=False)
    parser.add_argument('--ranged', action='store_true', help='Whether the character is ranged', default=False)
    parser.add_argument('--weapon-range', type=int, help='Minimum weapon range for the character', default=1)
    parser.add_argument('--level', type=int, help='Character level', default=200)
    parser.add_argument('--scrolled', action='store_true', help='Whether the character has scrolled items', default=False)
    parser.add_argument('--level-offset', type=int, help='Level offset for items', default=10)
    parser.add_argument('--ap', type=int, help='Action points for the character', default=12)
    parser.add_argument('--mp', type=int, help='Movement points for the character', default=6)
    parser.add_argument('--vit', type=int, help='Vitality for the character', default=4000)
    parser.add_argument('--res-neutral', type=int, help='Neutral resistance for the character', default=15)
    parser.add_argument('--res-fire', type=int, help='Fire resistance for the character', default=15)
    parser.add_argument('--res-air', type=int, help='Air resistance for the character', default=15)
    parser.add_argument('--res-water', type=int, help='Water resistance for the character', default=15)
    parser.add_argument('--res-earth', type=int, help='Earth resistance for the character', default=15)
    parser.add_argument('--crit', type=int, help='Critical chance for the character', default=0)

    # Character dictionaries
    parser.add_argument('--exo', type=str, nargs='+', help='Exos, e.g. "12:1 8:1"', default=[])
    parser.add_argument('--distributed-points', type=str, nargs='+', help='Distributed points for character attributes, e.g. "9: 595"', default=[])

    parser.add_argument('--path', type=str, help='Output path for the optimizer results', default=f'reports/{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}')
    if configure_parser is not None:
        configure_parser(parser)
    return parser.parse_args()

def _parse_lst_to_dict(lst):
    result = {}
    for item in lst:
        key, value = map(int, item.split(':'))
        result[int(key)] = int(value)
    return result

def get_config_from_args(args):
    config = {
        "optimizer" : {
            "language": "es",
            "population_size": args.population_size,
            "num_parents_mating": args.num_parents_mating, # Number of parents to mate, usually 1/3 of population sizeze
            "num_generations": args.num_generations,
            "mutation_rate": args.mutation_rate,
            "crossover_rate": args.crossover_rate,
            "parent_selection_type": "tournament",  # Tournament Selection
            "tournament_size": args.tournament_size,
            "exclusions": {
                "items": [6894,
                            6895,
                            3080,
                            9031,
                            6980, # Vulbis
                            13344, # Dolmanax
                            ] + args.exclusions,
            },
            "inclusions": {
                "items": [
                    # 14093, # Botas kuko
                    # 18718, # Escudo kuko
                    # 14092, # Anillo kuko
                    # 8993, # Espada maldita
                    # 7754, # Dofus ocre
                ] + args.inclusions,
            },
            "preferences": {
                "lower": {
                    12: {
                        "target": args.ap,  # AP
                        "strength": args.penalty_strength,  # Penalty for not meeting the target
                    },
                    8: {
                        "target": args.mp,  # MP
                        "strength": args.penalty_strength,  # Penalty for not meeting the target
                    },
                    9: {
                        "target": args.vit,  # Vit
                        "strength": args.penalty_strength,  # Penalty for not meeting the target
                    },
                    34 : {
                        "target": args.res_neutral, # %res neutral
                        "strength": args.penalty_strength,  # Penalty for not meeting the target
                    },
                    37 : {
                        "target": args.res_fire, # %res fire
                        "strength": args.penalty_strength,  # Penalty for not meeting the target
                    },
                    16 : {
                        "target": args.res_air, # %res air
                        "strength": args.penalty_strength,  # Penalty for not meeting the target
                    },
                    17 : {
                        "target": args.res_water, # %res water
                        "strength": args.penalty_strength,  # Penalty for not meeting the target
                    },
                    63 : {
                        "target": args.res_earth, # %res earth
                        "strength": args.penalty_strength,  # Penalty for not meeting the target
                    },
                    29: {
                        "target": args.crit, # Critical chance
                        "strength": args.penalty_strength,  # Penalty for not meeting the target
                    }
                },
                "upper": {},
            },

            "path": args.path,
            "level_offset": args.level_offset,  # Level offset for items
            "objective": args.objective,  # Objective to optimize, can be "weapon" or "elements"
            "normalize_by_apcost" : args.normalize_by_apcost, # If False, only care about absolute damage regardless of AP costst
        },
        "character": {
            "level": args.level,
            "scrolled": args.scrolled,
            "exo": _parse_lst_to_dict(args.exo),
            "distributed_points": _parse_lst_to_dict(args.distributed_points),
            "elements" : args.elements,
            "melee" : args.melee,
            "ranged" : args.weapon_range if args.ranged else False
        }
    }
    return config
