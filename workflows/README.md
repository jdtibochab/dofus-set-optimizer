
## Usage: Maestro workflows

[Maestro](https://maestrowf.readthedocs.io/) (installed as the `maestrowf` dependency) is used to keep each build's settings in a versioned YAML spec and give every run its own timestamped workspace with logs and the exact spec used.

### Running a workflow

```bash
cd workflows
maestro run workflow.hupper.yaml                     # asks for confirmation; add -y to skip
maestro run -p pgen.steamer.py workflow.steamer.yaml # specs with a parameter generator
maestro status report-steamer_*                      # check progress
```

`workflow.cra.yaml` and `workflow.steamer.yaml` take some variables (`$(OBJECTIVE)`, `$(MP)`, `$(HEALS)`, ...) from their `pgen.<build>.py` parameter generator, which runs one study step per combination of the lists defined at its top. Edit those lists to sweep settings; the launch command is also in each spec's `description`.

Each run creates `workflows/report-<name>_<YYYYMMDD-HHMMSS>/`. The optimizer outputs (`report.html`, `report.txt`, `summary.csv`, `pca.png`, `generations.png`, `config.json`) are in its `run_optimization/` subdirectory, alongside the step's stdout/stderr (`run_optimization.<pid>.out/.err`). With a parameter generator there is one `run_optimization/<params>/` folder per combination.

Once every optimization has finished, an `html_report` step writes `index.html` at the top of the study folder: one row per run with its parameter values, best fitness, targets met, best weapon and a link to the run's `report.html`. Open it to compare the runs of a sweep. It also rebuilds each run's `report.html`, so the reports always match the current report code.

### Included builds

| Spec | Objective | Elements | Weapon | Notes |
| --- | --- | --- | --- | --- |
| [workflow.cra.yaml](workflow.cra.yaml) + [pgen.cra.py](pgen.cra.py) | from pgen (`elements`) | from pgen | ranged, range ≥ 6 | High crit; pgen sets the objective, MP and element combinations to run. |
| [workflow.hupper.yaml](workflow.hupper.yaml) | `elements` | agi str cha int | ranged, range ≥ 3 | Spell-damage build, 12 AP / 6 MP. |
| [workflow.sacri-omni.yaml](workflow.sacri-omni.yaml) | `weapon` / AP | agi str cha int | melee | Multi-element hitter. |
| [workflow.sacri-tank.yaml](workflow.sacri-tank.yaml) | `steal` / AP | agi | melee | High vit, resistances, lock and initiative. |
| [workflow.steamer.yaml](workflow.steamer.yaml) + [pgen.steamer.py](pgen.steamer.py) | from pgen (`elements`) | int | melee + ranged | Intelligence build; pgen pairs each objective with a minimum `HEALS` (currently 200). |

### Heal optimization

Two ways to bring healing into a workflow:

- **Maximize healing:** set `OBJECTIVE: "heals"` (alone, or combined such as `"elements heals"`) and `ELEMENTS: "int"`. The score is `15 × (1 + Intelligence / 100) + Heals bonus`.
- **Require a minimum heal bonus:** keep your damage objective and set `HEALS` to the minimum flat Heals bonus; sets below it are penalized like any other stat target. `pgen.steamer.py` does this, zipping each entry of `OBJECTIVE` with the matching entry of `HEALS` (e.g. `OBJECTIVE = ["elements", "heals"]`, `HEALS = [200, 0]` runs a damage build with ≥ 200 Heals and a pure healer).

### Writing your own

Copy an existing spec and edit the variables in `env.variables`. Each one maps to the CLI flag of the same name (see [Arguments](../README.md#arguments)):

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
    HEALS: 0                      # minimum flat Heals bonus (0 = ignore)

    EXO: "ap:1 mp:1"              # or "none"
    DISTRIBUTED_POINTS: "none"
    SCROLLED: "true"
    REFERENCE: "none"             # space-separated IDs of a set to compare against

    ISLANDS: 16
    MAX_WORKERS: 8
    LANGUAGE: "en"              # en, es, fr, de or pt
```

Keep the `batch` and `study` sections unchanged. The `run_optimization` step `cd`s to `REPO_ROOT`, turns these variables into CLI flags (boolean variables add their flag when `"true"`, list variables are skipped when `"none"`), and calls `scripts/main.py` with `--path $(WORKSPACE)`. The `html_report` step depends on `run_optimization_*`, so it runs once after every parameter combination has finished, and calls `scripts/html_report.py $(OUTPUT_PATH)` on the whole study. Every variable referenced in the step must be defined in the spec. The specs use `batch: type: local`; switching to a scheduler such as SLURM is a matter of changing the `batch` block per the Maestro docs.
