from datetime import datetime 
import argparse
import os
import json

from optimizer import Optimizer
from chromosome import Chromosome
from character import Character
from utils import get_item_set, elements
from data import items, item_sets
import pandas as pd
from analysis import Analyzer

import matplotlib.pyplot as plt
from utils import base_config

def parse_args(configure_parser=None):
    """
    Build the command-line parser for the training workflow.

    Args:
        configure_parser (Any): Input value.

    Example:
        >>> parse_args(configure_parser=...)
    """
    parser = argparse.ArgumentParser(description="Run MLP embedding demo with different DBTL cycle splits")
    parser.add_argument('--keys', type=str, nargs='+', help='Keys to trigger different settings', default=None, required=True)
    parser.add_argument('--exo', type=str, nargs='+', help='Exos', default=[])
    parser.add_argument('--normalize-by-apcost', action='store_true', help='Whether to normalize damage by AP cost', default=False)
    parser.add_argument('--objective', type=str, help='Objective to optimize, can be "weapon" or "elements"', default="weapon")
    if configure_parser is not None:
        configure_parser(parser)
    return parser.parse_args()

def update_config_from_args(config, args):
    if 'crit' in args.keys:
        config['optimizer']['preferences']['lower'][29] = {
            "target": 80,  # Crit
            "strength": 0.1,  # Penalty for not meeting the target
        }
    if 'omni' in args.keys:
        config['character']['elements'] = [
            36, # Agility,
            22, # Chance
            13, # Intelligence
            45  # Strength
        ]
    if 'str' in args.keys:
        config['character']['elements'] = [
            45  # Strength
        ]
    if 'cha' in args.keys:
        config['character']['elements'] = [
            22, # Chance
        ]
    if 'int' in args.keys:
        config['character']['elements'] = [
            13, # Intelligence
        ]
    if 'agi' in args.keys:
        config['character']['elements'] = [
            36, # Agility,
        ]
    if 'vit' in args.keys:
        config['character']['distributed_points'] = {
            9: 595,  # Vitality
        }
    if 'ranged' in args.keys:
        config['character']['melee'] = False
        config['character']['ranged'] = 7
        config['optimizer']['preferences']['lower'][31] = {
            "target": 6, # range
            "strength": 0.1,  # Penalty for not meeting the target
        }
    if 'midranged' in args.keys:
        config['character']['ranged'] = 3
        config['optimizer']['preferences']['lower'][31] = {
            "target": 6, # range
            "strength": 0.1,  # Penalty for not meeting the target
        }
    if 'melee' in args.keys:
        config['character']['ranged'] = False

    if 'AP' in args.exo:
        config['character']['exo'][12] = 1
    if 'MP' in args.exo:
        config['character']['exo'][8] = 1
    if 'AL' in args.exo:
        config['character']['exo'][31] = 1
    if 'crit' in args.exo:
        config['character']['exo'][29] = 1

    # if args.normalize_by_apcost:
    #     config['optimizer']['normalize_by_apcost'] = True

    # Dump all other keys into optimizer
    for key, value in vars(args).items():
        config['optimizer'][key] = value

    return config

def _get_output_path(args):
    return f"reports/{"-".join(sorted(args.keys))}/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"


def _preprocess_items(config):
    dct = {}
    for k,v in items.items():
        item_set = get_item_set(v,item_sets)
        dct[k] = {
            "name" : v["name"][config["optimizer"]["language"]],
            "set" : item_set["name"][config["optimizer"]["language"]] if item_set else None,
            "level" : v["level"]
        }
        dct[k].update({i:j for i,j in v['type'].items() if i not in dct[k]})
    return pd.DataFrame.from_dict(dct, orient='index')

def main():
    print(f"[CHECKPOINT] Starting at {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")

    # Parse command-line arguments and override config values if provided
    args = parse_args(configure_parser=None)

    # Copy base config
    config = base_config.copy()

    # Update from keys
    config = update_config_from_args(config, args)

    # Update path
    config['optimizer']['path'] = _get_output_path(args)

    # Save configs
    if not os.path.exists(config["optimizer"]["path"]):
        os.makedirs(config["optimizer"]["path"], exist_ok=True)

    with open(config["optimizer"]["path"] + '/config.json', 'w') as file:
        json.dump(config, file, indent=4)

    # # Load items
    # Items = _preprocess_items(config)

    # Initialize objects
    char = Character(**config["character"])
    opt = Optimizer(char,
                    items,
                    item_sets,
                    **config["optimizer"])

    # Optimize
    solutions = opt.optimize(islands = 12, max_workers = 4)

    # Analyze
    analyzer = Analyzer(opt, solutions)
    analyzer.run_analysis()

    # Save results
    analyzer.report_extended_results()

    # Plot PCA
    analyzer.plot_pca()
    plt.savefig(f'{config['optimizer']['path']}/pca.png')

    # Plot generations
    analyzer.report_generations()
    plt.savefig(f'{config['optimizer']['path']}/generations.png')

    print(f"[CHECKPOINT] Finished at {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")

if __name__ == "__main__":
    main()