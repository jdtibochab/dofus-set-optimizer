
## Usage: Maestro workflows

[Maestro](https://maestrowf.readthedocs.io/) (installed as the `maestrowf` dependency) is used to keep each build's settings in a versioned YAML spec and give every run its own timestamped workspace with logs and the exact spec used.

### Running a workflow

```bash
cd workflows
maestro run cra.yaml          # asks for confirmation; add -y to skip
maestro status report-cra_*   # check progress
```

Each run creates `workflows/report-<name>_<YYYYMMDD-HHMMSS>/`; the optimizer outputs (`report.txt`, `summary.csv`, `pca.png`, `generations.png`, `config.json`) are in its `run_training/` subdirectory, alongside the step's stdout/stderr (`run_training.<pid>.out/.err`).

### Included builds

| Spec | Objective | Elements | Weapon | Notes |
| --- | --- | --- | --- | --- |
| [cra.yaml](workflows/cra.yaml) | `weapon` / AP | agi str cha int | ranged, range ≥ 6 | High crit, 12 AP / 5 MP. |
| [hupper.yaml](workflows/hupper.yaml) | `elements` | agi str cha int | ranged, range ≥ 3 | Spell-damage build, 12 AP / 6 MP. |
| [sacri-omni.yaml](workflows/sacri-omni.yaml) | `weapon` / AP | agi str cha int | melee | Multi-element hitter. |
| [sacri-tank.yaml](workflows/sacri-tank.yaml) | `steal` / AP | agi | melee | High vit, resistances, lock and initiative. |
| [steamer.yaml](workflows/steamer.yaml) | `elements` + `push` | agi cha | melee + ranged | Spell + push-damage build, push target 500. |

### Writing your own

Copy an existing spec and edit the variables in `env.variables`. Each one maps to the CLI flag of the same name (see [Arguments](#arguments)):

```yaml
description:
  name: report-my-build          # workspace prefix
  description: Configuration for Dofus set optimization

env:
  variables:
    REPO_ROOT: $(SPECROOT)/..

    OBJECTIVE: "weapon"            # space-separated list; scores are summed
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
    # RES_*, RANGE, LOCK, DODGE, INITIATIVE, PUSH, CRIT ...

    EXO: "ap:1 mp:1"              # or "none"
    DISTRIBUTED_POINTS: "none"
    SCROLLED: "true"
    REFERENCE: "none"             # space-separated IDs of a set to compare against

    ISLANDS: 16
    MAX_WORKERS: 8
    LANGUAGE: "en"              # en, es, fr, de or pt
```

Keep the `batch` and `study` sections unchanged: the single `run_training` step `cd`s to `REPO_ROOT`, turns these variables into CLI flags (boolean variables add their flag when `"true"`, list variables are skipped when `"none"`), and calls `scripts/main.py` with `--path $(WORKSPACE)`. Every variable referenced in the step must be defined in the spec. The specs use `batch: type: local`; switching to a scheduler such as SLURM is a matter of changing the `batch` block per the Maestro docs.
