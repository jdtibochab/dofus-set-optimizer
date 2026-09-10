import json
import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd

from analysis import Analyzer
from character import Character
from chromosome import Chromosome
from data import item_sets, items
from optimizer import Optimizer
from utils import get_config_from_args, get_item_set, parse_args


def update_config_from_args(config, args):
    if 'crit' in args.keys:
        config['optimizer']['preferences']['lower'][29] = {
            "target": 85,  # Crit
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
            "target": 4, # range
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
    if args.include_items:
        config['optimizer']['inclusions']['items'].extend([int(i) for i in args.include_items])
    if args.exclude_items:
        config['optimizer']['exclusions']['items'].extend([int(i) for i in args.exclude_items])

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
    config = get_config_from_args(args)

    # # Update from keys
    # config = update_config_from_args(config, args)

    # # Update path
    # config['optimizer']['path'] = _get_output_path(args)

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

    # Run analysis
    analyzer.run_analysis()

    # Add reference to analyzer if provided
    if config['optimizer'].get('reference'):
        chr = Chromosome(
            [int(i) for i in config['optimizer']['reference']], opt)
        analyzer.candidates.insert(0, chr)

    # Save extended results
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