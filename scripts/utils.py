
import argparse
from datetime import datetime


elements = [
    36, # Agility,
    22, # Chance
    13, # Intelligence
    45, # Strength
]

_key_to_id = {
    "agi": 36,
    "cha": 22,
    "int": 13,
    "str": 45,
    "vit": 9,
    "wis": 10,

    "ap": 12,
    "mp": 8,
    "res_air": 16,
    "res_water": 17,
    "res_fire": 37,
    "res_earth": 63,
    "res_neutral": 34,
    "crit": 29,
    "range": 31,
    "initiative": 24,
    "lock": 26,
    "dodge": 59,
    "pow": 32
}

steal_damages = [224, 203, 193, 221, 223, 257]

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

    # Process set effects for the given overlap
    if set_effects is not None:
        for d in set_effects.get(str(overlap), []):
            field = "max" if d["min_max_irrelevant"] == 0 else "min"
            contributions[d["element_id"]] = d[field]
    
    # Starting v3.7, set bonus contribution is calculated as 1 for every set with at least 2 pieces
    contributions[72] = int(overlap >= 2)
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
    parser = argparse.ArgumentParser(description="Run the Dofus set optimization workflow")

    # Optimizer
    parser.add_argument('--normalize-by-apcost', action='store_true', help='Whether to normalize damage by AP cost', default=False)
    parser.add_argument('--objective', type=str, help='Objective to optimize, can be "weapon" or "elements"', default="weapon", choices=["weapon", "elements", "steal", "push"])

    parser.add_argument('--reference', type=str, nargs='+', help='Reference items', default=[])
    parser.add_argument('--population-size', type=int, help='Population size for the optimizer', default=100)
    parser.add_argument('--num-parents-mating', type=int, help='Number of parents to mate', default=150)
    parser.add_argument('--num-generations', type=int, help='Number of generations', default=300)
    parser.add_argument('--mutation-type', type=str, help='Mutation type for the optimizer', default="adaptive")
    parser.add_argument('--mutation-rate', type=float, nargs='+', help='Mutation rate', default=[0.1875, 0.0625])
    parser.add_argument('--crossover-rate', type=float, help='Crossover rate', default=0.85)
    parser.add_argument('--tournament-size', type=int, help='Tournament size for selection', default=3)
    parser.add_argument('--penalty-strength', type=float, help='Penalty for strength', default=0.01)
    parser.add_argument('--keep-elitism', type=int, help='Keep elitism for the optimizer', default=2)
    parser.add_argument('--crossover-type', type=str, help='Crossover type for the optimizer', default="single_point")

    parser.add_argument('--islands', type=int, help='Number of islands for the optimizer', default=1)
    parser.add_argument('--max-workers', type=int, help='Maximum number of workers for parallel execution', default=1)

    # Items and characteristics
    parser.add_argument('--exclusions', type=int, nargs='+', help='Items to exclude', default=[])
    parser.add_argument('--inclusions', type=int, nargs='+', help='Items to include', default=[])
    parser.add_argument('--elements', type=str, nargs='+', help='Character elements', default=["agi", "str", "cha", "int"])
    parser.add_argument('--melee', action='store_true', help='Whether the character is melee', default=False)
    parser.add_argument('--ranged', action='store_true', help='Whether the character is ranged', default=False)
    parser.add_argument('--weapon-range', type=int, help='Minimum weapon range for the character', default=1)
    parser.add_argument('--level', type=int, help='Character level', default=200)
    parser.add_argument('--scrolled', action='store_true', help='Whether the character has scrolled items', default=False)
    parser.add_argument('--level-offset', type=int, help='Level offset for items', default=10)
    parser.add_argument('--ap', type=int, help='Action points for the character', default=7)
    parser.add_argument('--mp', type=int, help='Movement points for the character', default=3)
    parser.add_argument('--vit', type=int, help='Vitality for the character', default=3000)
    parser.add_argument('--res-neutral', type=int, help='Neutral resistance for the character', default=0)
    parser.add_argument('--res-fire', type=int, help='Fire resistance for the character', default=0)
    parser.add_argument('--res-air', type=int, help='Air resistance for the character', default=0)
    parser.add_argument('--res-water', type=int, help='Water resistance for the character', default=0)
    parser.add_argument('--res-earth', type=int, help='Earth resistance for the character', default=0)
    parser.add_argument('--crit', type=int, help='Critical chance for the character', default=0)
    parser.add_argument('--range', type=int, help='Range for the character', default=0)
    parser.add_argument('--lock', type=int, help='Lock for the character', default=0)
    parser.add_argument('--dodge', type=int, help='Dodge for the character', default=0)
    parser.add_argument('--initiative', type=int, help='Initiative for the character', default=0)

    # Character dictionaries
    parser.add_argument('--exo', type=str, nargs='+', help='Exos, e.g. "12:1 8:1"', default=[])
    parser.add_argument('--distributed-points', type=str, nargs='+', help='Distributed points for character attributes, e.g. "9: 595"', default=[])

    # I/O
    parser.add_argument('--path', type=str, help='Output path for the optimizer results', default=f'reports/{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}')
    parser.add_argument('--config', type=str, help='Path to the configuration file', default=None)
    parser.add_argument('--language', type=str, help='Language for item and stat names in reports', default="en", choices=["en", "es", "fr", "de", "pt"])

    if configure_parser is not None:
        configure_parser(parser)
    return parser.parse_args()

def _parse_lst_to_dict(lst):
    result = {}
    for item in lst:
        key, value = map(str, item.split(':'))
        result[_key_to_id[key]] = int(value)
    return result

def get_bounds_from_args(args):
    bound = {}
    for key, value in vars(args).items():
        if key not in _key_to_id:
            continue
        if value <= 0:
            continue
        _id = _key_to_id[key]
        bound[_id] = {
            "target": value,
            "strength": args.penalty_strength
        }
    return bound

def get_config_from_args(args):
    config = {
        "optimizer" : {
            "language": args.language,
            "population_size": args.population_size,
            "num_parents_mating": args.num_parents_mating, # Number of parents to mate, usually 1/3 of population sizeze
            "num_generations": args.num_generations,
            "mutation_rate": args.mutation_rate,
            "crossover_rate": args.crossover_rate,
            "parent_selection_type": "tournament",  # Tournament Selection
            "tournament_size": args.tournament_size,
            "keep_elitism": args.keep_elitism,
            "mutation_type": args.mutation_type,
            "crossover_type": args.crossover_type,
            "max_workers": args.max_workers,
            "islands": args.islands,
            "exclusions": {
                "items": [6894,
                            6895,
                            3080,
                            9031,
                            6980, # Vulbis
                            13344, # Dolmanax
                            29136, # Silvestre
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
                "lower": get_bounds_from_args(args),
                "upper": {},
            },

            "path": args.path,
            "level_offset": args.level_offset,  # Level offset for items
            "objective": args.objective,  # Objective to optimize, can be "weapon" or "elements"
            "normalize_by_apcost" : args.normalize_by_apcost, # If False, only care about absolute damage regardless of AP costst
            "reference": args.reference,  # Reference items
        },
        "character": {
            "level": args.level,
            "scrolled": args.scrolled,
            "exo": _parse_lst_to_dict(args.exo),
            "distributed_points": _parse_lst_to_dict(args.distributed_points),
            "elements" : [_key_to_id[key] for key in args.elements],
            "melee" : args.melee,
            "ranged" : args.weapon_range if args.ranged else False
        }
    }
    return config
