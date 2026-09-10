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