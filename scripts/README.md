
## Repository contents

| Path | Description |
| --- | --- |
| [scripts/main.py](scripts/main.py) | CLI entry point: parses arguments, builds the character and optimizer, runs the GA and writes the reports. |
| [scripts/utils.py](scripts/utils.py) | Argument parser (`parse_args`), CLI → config translation (`get_config_from_args`), stat ID tables and item/set contribution helpers. |
| [scripts/data.py](scripts/data.py) | Loads `data/MAPPED_ITEMS.json` and `data/MAPPED_SETS.json` into `items` and `item_sets` dicts keyed by Ankama ID. |
| [scripts/character.py](scripts/character.py) | `Character`: base stats from level, characteristic point distribution (respecting soft caps), scrolls and exos. |
| [scripts/optimizer.py](scripts/optimizer.py) | `Optimizer`: filters valid items, builds the per-slot item pools, seeds the population from item sets and runs [PyGAD](https://pygad.readthedocs.io/) (optionally across multiple islands/processes). |
| [scripts/chromosome.py](scripts/chromosome.py) | `Chromosome`: one candidate set. Computes stat totals (items + set bonuses + character), damage, item-condition checks, penalties and fitness. |
| [scripts/analysis.py](scripts/analysis.py) | `Analyzer`: selects candidate solutions, writes `report.txt` / `summary.csv`, and plots PCA and per-island fitness curves. |
| [notebooks/Items.ipynb](notebooks/Items.ipynb) | Notebook for interactively inspecting items and evaluating hand-picked sets (adds `scripts/` to `sys.path`; run with the repo root as working directory). |
| [workflows/](workflows/) | [Maestro](https://maestrowf.readthedocs.io/) study specs with ready-made builds (`cra`, `hupper`, `sacri-omni`, `sacri-tank`, `steamer`). |
| [download.sh](download.sh) | Downloads the latest Dofus 3 game data release from [dofusdude/dofus3-main](https://github.com/dofusdude/dofus3-main). |
| [setup.py](setup.py) | Package metadata and dependencies. |

Generated, git-ignored directories: `data/` (game data), `reports/` (CLI runs), `debug/` (runs launched from the VS Code debugger) and `workflows/report-*` (Maestro runs).

## How it works

**Chromosome layout.** A set is a vector of 16 Ankama item IDs, one per slot:

| Slot(s) | Item type |
| --- | --- |
| 0 | Amulet |
| 1 | Weapon |
| 2–3 | Rings |
| 4 | Belt |
| 5 | Boots |
| 6 | Shield |
| 7 | Hat |
| 8 | Cloak |
| 9 | Pet / mount |
| 10–15 | Dofus / trophies (prysmaradites are excluded) |

**Item filtering.** An item is a candidate only if:
- it is not excluded (via `--exclusions` or the built-in list in [scripts/utils.py](scripts/utils.py)),
- its level is ≤ the character level and, except for pets, mounts and Dofus, ≥ `level - level_offset`,
- weapons match the `--melee` / `--ranged` / `--weapon-range` constraints and cost more than 0 AP.

Items passed with `--inclusions` are forced into their slot (the pool for that slot is reduced to that single item).

**Fitness.** Depends on `--objective`:

| Objective | Fitness |
| --- | --- |
| `weapon` | Expected weapon hit damage across the selected elements (crit-weighted when `--crit` is set). With `--normalize-by-apcost`, divided by the weapon's AP cost. |
| `elements` | Expected damage of a generic 20-base-damage spell in each selected element. |
| `steal` | Like `weapon`, but only counting the weapon's life-steal lines. |
| `push` | Total push damage. |

The raw fitness is then penalized:
- ×0.1 for each duplicated Dofus/trophy, duplicated rings, or any item whose equip conditions are not met by the set's totals;
- for every stat target you set (e.g. `--ap 12`, `--res-fire 20`), a smooth multiplicative penalty that grows with the relative shortfall, scaled by `--penalty-strength`.

Stat targets are **lower bounds**; passing `0` (the default for most) means "don't care".

**Search.** The initial population is seeded with one chromosome per item set (filling slots with that set's pieces), topped up with random sets. Each island runs PyGAD with tournament selection, elitism and adaptive mutation. With `--islands N --max-workers M`, N islands run across M processes.

**Analysis.** From every island's history of best solutions, all unique, unpenalized sets within 90% of the global best fitness are kept as candidates and reported, best first.