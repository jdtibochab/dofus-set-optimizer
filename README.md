# Dofus set optimizer

A genetic-algorithm optimizer that searches the full Dofus 3 item database for the equipment set that maximizes a chosen objective (weapon damage, spell damage, steal damage or push damage) for a given character, while softly enforcing stat targets such as AP, MP, vitality, resistances, crit, lock or initiative.

The optimizer runs several independent "islands" Genetic Algorithm optimizations in parallel, collects the best unique, unpenalized sets found across them, and writes a human-readable report, a CSV comparison table and diagnostic plots.

## Repository contents

| Path | Description |
| --- | --- |
| [main.py](main.py) | CLI entry point: parses arguments, builds the character and optimizer, runs the GA and writes the reports. |
| [utils.py](utils.py) | Argument parser (`parse_args`), CLI → config translation (`get_config_from_args`), stat ID tables and item/set contribution helpers. |
| [data.py](data.py) | Loads `data/MAPPED_ITEMS.json` and `data/MAPPED_SETS.json` into `items` and `item_sets` dicts keyed by Ankama ID. |
| [character.py](character.py) | `Character`: base stats from level, characteristic point distribution (respecting soft caps), scrolls and exos. |
| [optimizer.py](optimizer.py) | `Optimizer`: filters valid items, builds the per-slot item pools, seeds the population from item sets and runs [PyGAD](https://pygad.readthedocs.io/) (optionally across multiple islands/processes). |
| [chromosome.py](chromosome.py) | `Chromosome`: one candidate set. Computes stat totals (items + set bonuses + character), damage, item-condition checks, penalties and fitness. |
| [analysis.py](analysis.py) | `Analyzer`: selects candidate solutions, writes `report.txt` / `summary.csv`, and plots PCA and per-island fitness curves. |
| [Items.ipynb](Items.ipynb) | Notebook for interactively inspecting items and evaluating hand-picked sets. |
| [workflows/](workflows/) | [Maestro](https://maestrowf.readthedocs.io/) study specs with ready-made builds (`cra`, `hupper`, `sacri-omni`, `sacri-tank`, `steamer`). |
| [runs.sh](runs.sh) | Runs all the Maestro workflows in sequence. |
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
- it is not excluded (via `--exclusions` or the built-in list in [utils.py](utils.py)),
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

## Installation

Requires Python ≥ 3.10 (f-string syntax in [main.py](main.py) needs 3.12) and the [GitHub CLI](https://cli.github.com/) for downloading game data.

```bash
git clone https://github.com/jdtibochab/dofus-set-optimizer.git
cd dofus-set-optimizer
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Download the game data into data/ (needs `gh auth login` first)
bash download.sh
```

Only `data/MAPPED_ITEMS.json` and `data/MAPPED_SETS.json` are needed; the rest of the release can be deleted. Re-run `download.sh` after game updates to refresh the item database.

## Usage: CLI

Always run from the repository root: the data files are loaded with relative paths.

Minimal example — a level 200, 4-element character optimizing weapon damage per AP, targeting 12 AP / 6 MP:

```bash
python main.py --objective weapon --normalize-by-apcost \
    --elements agi str cha int --level 200 --scrolled \
    --ap 12 --mp 6 --vit 4000 \
    --islands 8 --max-workers 8
```

A fuller example (melee agility tank maximizing steal damage):

```bash
python main.py \
    --objective steal --normalize-by-apcost \
    --elements agi --melee \
    --level 200 --level-offset 10 --scrolled \
    --ap 12 --mp 5 --vit 4000 \
    --res-neutral 20 --res-fire 20 --res-air 20 --res-water 20 --res-earth 20 \
    --lock 150 --dodge 60 --initiative 3200 \
    --exo ap:1 mp:1 vit:200 \
    --inclusions 7754 7115 18043 \
    --exclusions 32121 \
    --islands 16 --max-workers 8 \
    --path reports/sacri-tank
```

### Arguments

**Objective**

| Flag | Default | Description |
| --- | --- | --- |
| `--objective` | `weapon` | One of `weapon`, `elements`, `steal`, `push`. |
| `--normalize-by-apcost` | off | Divide weapon damage by weapon AP cost. |

**Character**

| Flag | Default | Description |
| --- | --- | --- |
| `--level` | `200` | Character level. |
| `--elements` | `agi str cha int` | Damage elements to optimize (`agi`, `str`, `cha`, `int`). Characteristic points are split evenly across them unless `--distributed-points` is given. |
| `--scrolled` | off | Add +100 to every characteristic. |
| `--exo KEY:VALUE ...` | none | Exo bonuses, e.g. `ap:1 mp:1 range:1 vit:200`. |
| `--distributed-points KEY:VALUE ...` | auto | Characteristic points to invest per stat (soft caps applied), e.g. `vit:995`. |
| `--melee` / `--ranged` | off | Allow melee and/or ranged weapons. |
| `--weapon-range` | `1` | Minimum max-range of the weapon when `--ranged` is set. |

Keys accepted by `--exo` and `--distributed-points`: `agi`, `cha`, `int`, `str`, `vit`, `wis`, `ap`, `mp`, `range`, `crit`, `pow`, `initiative`, `lock`, `dodge`, `res_neutral`, `res_fire`, `res_air`, `res_water`, `res_earth`.

**Stat targets** (lower bounds; `0` = ignore). `--crit` also enables crit weighting in the damage formula.

`--ap` (default 7), `--mp` (3), `--vit` (3000), `--range`, `--crit`, `--lock`, `--dodge`, `--initiative`, `--res-neutral`, `--res-fire`, `--res-air`, `--res-water`, `--res-earth` (all default 0).

**Items**

| Flag | Default | Description |
| --- | --- | --- |
| `--level-offset` | `10` | Ignore gear more than this many levels below the character (pets, mounts and Dofus are exempt). |
| `--inclusions ID ...` | none | Ankama IDs to force into the set (e.g. a Dofus or a specific weapon). |
| `--exclusions ID ...` | none | Ankama IDs to never use (e.g. items you can't obtain). |
| `--reference ID ...` | none | A set to evaluate and add as entry 0 of the report, to compare against the optimizer's results. |

**Genetic algorithm**

| Flag | Default | Description |
| --- | --- | --- |
| `--population-size` | `100` | Chromosomes per generation. |
| `--num-generations` | `300` | Generations per island. |
| `--num-parents-mating` | `150` | Parents selected per generation. |
| `--tournament-size` | `3` | Tournament selection size. |
| `--keep-elitism` | `2` | Best solutions carried over unchanged. |
| `--crossover-type` / `--crossover-rate` | `single_point` / `0.85` | Crossover settings. |
| `--mutation-type` / `--mutation-rate` | `adaptive` / `0.1875 0.0625` | Mutation settings (adaptive takes two rates: low- and high-fitness). |
| `--penalty-strength` | `0.01` | Weight of the stat-target penalties. |
| `--islands` | `1` | Number of independent GA runs. |
| `--max-workers` | `1` | Parallel processes for the islands. |

**Output**

| Flag | Default | Description |
| --- | --- | --- |
| `--path` | `reports/<timestamp>` | Output directory. |

### Outputs

Each run writes to `--path`:

| File | Content |
| --- | --- |
| `config.json` | Full resolved configuration. |
| `report.txt` | One block per candidate set: fitness, weapon and spell damage, targeted stats, characteristics, item list (type, name, level, ID), any penalties, and the chromosome as a list of IDs. |
| `summary.csv` | All stat totals side by side, one column per candidate — handy for comparing sets in a spreadsheet. |
| `pca.png` | PCA of the candidates' stat totals, colored by fitness, with the top stat loadings drawn as arrows. Shows how different the good sets are from each other. |
| `generations.png` | Best fitness per generation for each island, to check convergence. |

Item and stat names are reported in Spanish (`language` is set to `es` in `get_config_from_args`, [utils.py](utils.py)); the data also contains `en`, `fr`, `de`, `pt`.

### Finding item IDs

Inclusions, exclusions and references use Ankama item IDs. Look them up in the `ankama_id` field of `data/MAPPED_ITEMS.json`, from [Items.ipynb](Items.ipynb), or from the last block of a previous `report.txt`. A quick search by name:

```bash
python -c "
from data import items
q = 'Ochre Dofus'
for i, it in items.items():
    if q.lower() in it['name']['en'].lower(): print(i, it['name']['en'], it['level'])
"
```

## Usage: Maestro workflows

[Maestro](https://maestrowf.readthedocs.io/) (installed as the `maestrowf` dependency) is used to keep each build's settings in a versioned YAML spec and give every run its own timestamped workspace with logs and the exact spec used.

### Running a workflow

```bash
cd workflows
maestro run cra.yaml          # asks for confirmation; add -y to skip
maestro status report-cra_*   # check progress
```

Or run all of them in sequence:

```bash
cd workflows
bash ../runs.sh
```

Each run creates `workflows/report-<name>_<YYYYMMDD-HHMMSS>/`; the optimizer outputs (`report.txt`, `summary.csv`, `pca.png`, `generations.png`, `config.json`) are in its `run_training/` subdirectory, alongside the step's stdout/stderr (`run_training.<pid>.out/.err`).

### Included builds

| Spec | Objective | Elements | Weapon | Notes |
| --- | --- | --- | --- | --- |
| [cra.yaml](workflows/cra.yaml) | `weapon` / AP | agi str cha int | ranged, range ≥ 6 | High crit, 12 AP / 5 MP. |
| [hupper.yaml](workflows/hupper.yaml) | `elements` | agi str cha int | ranged, range ≥ 3 | Spell-damage build, 12 AP / 6 MP. |
| [sacri-omni.yaml](workflows/sacri-omni.yaml) | `weapon` / AP | agi str cha int | melee | Multi-element hitter. |
| [sacri-tank.yaml](workflows/sacri-tank.yaml) | `steal` / AP | agi | melee | High vit, resistances, lock and initiative. |
| [steamer.yaml](workflows/steamer.yaml) | `push` | agi cha | melee + ranged | Push-damage build. |

### Writing your own

Copy an existing spec and edit the variables in `env.variables`. Each one maps to the CLI flag of the same name (see [Arguments](#arguments)):

```yaml
description:
  name: report-my-build          # workspace prefix
  description: Configuration for Dofus set optimization

env:
  variables:
    REPO_ROOT: $(SPECROOT)/..

    OBJECTIVE: "weapon"
    NORMALIZE_BY_APCOST: "true"
    EXCLUSIONS: "32121"           # space-separated IDs, or "none"
    INCLUSIONS: "7754 18043"      # space-separated IDs, or "none"

    ELEMENTS: "str int"
    MELEE: "true"
    RANGED: "false"
    WEAPON_RANGE: "none"          # minimum weapon range, or "none"

    LEVEL: 200
    LEVEL_OFFSET: 10
    AP: 12
    MP: 6
    VIT: 4000
    # RES_*, RANGE, LOCK, DODGE, INITIATIVE, CRIT ...

    EXO: "ap:1 mp:1"              # or "none"
    DISTRIBUTED_POINTS: "none"
    SCROLLED: "true"
    REFERENCE: "none"             # space-separated IDs of a set to compare against

    ISLANDS: 16
    MAX_WORKERS: 8
```

Keep the `batch` and `study` sections unchanged: the single `run_training` step `cd`s to `REPO_ROOT`, turns these variables into CLI flags (boolean variables add their flag when `"true"`, list variables are skipped when `"none"`), and calls `main.py` with `--path $(WORKSPACE)`. Every variable referenced in the step must be defined in the spec. The specs use `batch: type: local`; switching to a scheduler such as SLURM is a matter of changing the `batch` block per the Maestro docs.

## Tips

- **Runtime** scales with `islands × num_generations × population_size`. Start with `--islands 4 --num-generations 100` to check a configuration, then scale up.
- **Unmet targets**: if every result reports penalties for a stat, the target may be unreachable with your inclusions/exclusions. Lower it, or raise `--penalty-strength` to make it weigh more.
- **Comparing to your current set**: pass it as `--reference`; it appears as `Solution 0` in `report.txt` and in `summary.csv`.
- **Debugging**: when launched from the VS Code debugger, [main.py](main.py) writes to `debug/<timestamp>/` and forces the `push` objective.
