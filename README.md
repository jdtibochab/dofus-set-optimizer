# Dofus set optimizer

**Problem:** _A level 200 character has 10<sup>34</sup> ways to build a set, but there is only one that's good enough_

This is a fun project I developed in my free time that I used to learn Genetic Algorithm optimization in large phase spaces. I spent some extra time updating it with new code, but this is not a fully-fledged user-friendly codebase. That said, a programming-savvy Dofus enthusiast should be able to optimize their set using this code. You can use the python script in `scripts/main.py` to run it (see usage below), or the Maestro workflows in `worklows/`. If using Maestro, be sure to check their documentation first.

Feel free to contribute!

## Description of this repo
This repo contains a genetic-algorithm optimizer that searches the full Dofus 3 item database for the equipment set that maximizes one or more objectives (weapon damage, spell damage, steal damage, push damage or healing, summed when combined) for a given character, while softly enforcing stat targets such as AP, MP, vitality, resistances, crit, lock, initiative, push damage or a minimum heal bonus.

The optimizer runs several independent "islands" Genetic Algorithm ([PyGAD](https://pygad.readthedocs.io/)) optimizations in parallel, collects the best unique, unpenalized sets found across them, and writes a human-readable report, a CSV comparison table and diagnostic plots. The data is obtained from [dofusdude](https://github.com/dofusdude/dofus3-main).


## Installation

Requires Python ≥ 3.10 (f-string syntax in [scripts/main.py](scripts/main.py) needs 3.12) and the [GitHub CLI](https://cli.github.com/) for downloading game data.

```bash
# Clone the repo
git clone https://github.com/jdtibochab/dofus-set-optimizer.git

# Install 
pip install -e .

# Download the game data into data/ (needs `gh auth login` first)
bash download.sh
```

Alternatively, manually download them from the [releases](https://github.com/dofusdude/dofus3-main/releases)

Only `data/MAPPED_ITEMS.json` and `data/MAPPED_SETS.json` are needed; the rest of the release can be deleted. Re-run `download.sh` after game updates to refresh the item database.

## Usage: CLI

Commands below are run from the repository root (the default `--path` is `reports/<timestamp>` relative to the current directory). The data files are located relative to the scripts, so `scripts/main.py` can be called from anywhere.

Minimal example — a level 200, 4-element character optimizing weapon damage per AP, targeting 12 AP / 6 MP:

```bash
python scripts/main.py --objective weapon --normalize-by-apcost \
    --elements agi str cha int --level 200 --scrolled \
    --ap 12 --mp 6 --vit 4000 \
    --islands 8 --max-workers 8
```

A healer, maximizing healing with all characteristic points in Intelligence:

```bash
python scripts/main.py --objective heals \
    --elements int --melee --ranged \
    --level 200 --scrolled --ap 12 --mp 6 --vit 4000 \
    --islands 8 --max-workers 8
```

A damage dealer that also needs a minimum heal bonus (spell damage is maximized; sets below 200 Heals are penalized):

```bash
python scripts/main.py --objective elements --heals 200 \
    --elements int --melee --ranged \
    --level 200 --scrolled --ap 12 --mp 6 \
    --islands 8 --max-workers 8
```

A fuller example (melee agility tank maximizing steal damage):

```bash
python scripts/main.py \
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
| `--objective` | `weapon` | One or more of `weapon`, `elements`, `steal`, `push`, `heals`. With several (e.g. `--objective elements push`), their scores are added together before penalties are applied. Scores are not rescaled, so damage objectives (typically 1000+) outweigh push and heals (typically a few hundred). |
| `--normalize-by-apcost` | off | Divide weapon damage by weapon AP cost. |

What each objective scores:

| Objective | Score |
| --- | --- |
| `weapon` | Expected weapon hit damage across the selected elements (crit-weighted when `--crit` is set); divided by AP cost with `--normalize-by-apcost`. |
| `elements` | Expected damage of a generic 20-base-damage spell in each selected element. |
| `steal` | Like `weapon`, counting only the weapon's life-steal lines. |
| `push` | Push damage of a 2-cell push: `(level / 2 + push damage bonus + 32) × 2`. |
| `heals` | Healing of a reference 15-base heal: `15 × (1 + Intelligence / 100) + Heals bonus`. Use `--elements int` so characteristic points go to Intelligence. |

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

Keys accepted by `--exo` and `--distributed-points`: `agi`, `cha`, `int`, `str`, `vit`, `wis`, `ap`, `mp`, `range`, `crit`, `pow`, `initiative`, `lock`, `dodge`, `push`, `heals`, `res_neutral`, `res_fire`, `res_air`, `res_water`, `res_earth`.

**Stat targets** (lower bounds; `0` = ignore). `--crit` also enables crit weighting in the damage formula. `--heals` sets a minimum flat Heals bonus (stat 121, "Soin" / "de cura"); it works with any objective, so a damage build can be required to keep some healing.

`--ap` (default 7), `--mp` (3), `--vit` (3000), `--range`, `--crit`, `--lock`, `--dodge`, `--initiative`, `--push`, `--heals`, `--res-neutral`, `--res-fire`, `--res-air`, `--res-water`, `--res-earth` (all default 0).

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
| `--language` | `en` | Language for item and stat names in the reports: `en`, `es`, `fr`, `de`, `pt`. |

### Outputs

Each run writes to `--path`:

| File | Content |
| --- | --- |
| `config.json` | Full resolved configuration. |
| `report.txt` | One block per candidate set: fitness, weapon, spell and push damage, healing, targeted stats, characteristics, item list (type, name, level, ID), any penalties, and the chromosome as a list of IDs. |
| `summary.csv` | All stat totals side by side, one column per candidate — handy for comparing sets in a spreadsheet. |
| `pca.png` | PCA of the candidates' stat totals, colored by fitness, with the top stat loadings drawn as arrows. Shows how different the good sets are from each other. |
| `generations.png` | Best fitness per generation for each island, to check convergence. |

Item and stat names are reported in the language chosen with `--language` (English by default).

### Finding item IDs

Inclusions, exclusions and references use Ankama item IDs. Look them up in the `ankama_id` field of `data/ITEM_NAMES_AND_IDS.<language>.csv` (generated by `python -m scripts.data` from the repo root).

## Usage: Maestro workflows

[Maestro](https://maestrowf.readthedocs.io/) (installed as the `maestrowf` dependency) is used to keep each build's settings in a versioned YAML spec and give every run its own timestamped workspace with logs and the exact spec used.

### Running a workflow

```bash
cd workflows
maestro run workflow.hupper.yaml                     # asks for confirmation; add -y to skip
maestro run -p pgen.steamer.py workflow.steamer.yaml # specs with a parameter generator
```

See [workflows/README.md](workflows/README.md) for the included builds, parameter generators, heal optimization and writing your own spec.

Each run creates `workflows/report-<name>_<YYYYMMDD-HHMMSS>/`; the optimizer outputs (`report.txt`, `summary.csv`, `pca.png`, `generations.png`, `config.json`) are in its `run_training/` subdirectory, alongside the step's stdout/stderr (`run_training.<pid>.out/.err`).

## Tips

- **Runtime** scales with `islands × num_generations × population_size`. Start with `--islands 4 --num-generations 100` to check a configuration, then scale up.
- **Unmet targets**: if every result reports penalties for a stat, the target may be unreachable with your inclusions/exclusions. Lower it, or raise `--penalty-strength` to make it weigh more.
- **Comparing to your current set**: pass it as `--reference`; it appears as `Solution 0` in `report.txt` and in `summary.csv`.
- **Debugging**: when launched from the VS Code debugger, [scripts/main.py](scripts/main.py) writes to `debug/<timestamp>/` and forces the `push` objective.
