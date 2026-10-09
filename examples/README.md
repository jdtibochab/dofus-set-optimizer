# Examples

Three finished Maestro runs, kept here so you can see what the optimizer produces without running it. Each folder is a complete Maestro workspace (spec, parameter generator, logs and optimizer outputs) copied from `workflows/report-<name>_<timestamp>/`.

All three are level 200, fully scrolled characters at 12 AP with 16 islands × 300 generations. Reports are in Spanish (`LANGUAGE: "es"`), so stats show up as e.g. `PA` (AP), `PM` (MP), `vitalidad`, `placaje` (lock), `huida` (dodge) and `de cura` (Heals).

| Example | Build | Objective | Key targets | Reference set | Best fitness |
| --- | --- | --- | --- | --- | --- |
| [int-heals](#int-heals) | Intelligence hybrid (steamer) | `elements` | 6 MP, 6 range, ≥ 200 Heals | none | 1858 |
| [long-range-multi-crit](#long-range-multi-crit) | 4-element ranged crit (cra) | `elements` | 5 MP, 6 range, 87% crit | yes (2040) | 2221 |
| [tank-lock](#tank-lock) | Agility melee tank (sacri) | `steal` / AP | 5 MP, 4000 vit, 20% res, 150 lock, 3200 initiative | yes (833) | 852 |

## Folder layout

| Path | Content |
| --- | --- |
| `workflow.<name>.yaml` / `<name>.yaml` | The exact Maestro spec used for the run. |
| `pgen.<name>.py` | Parameter generator that fills `$(OBJECTIVE)`, `$(MP)`, etc. (not used by tank-lock). |
| `run_optimization/<params>/` or `run_training/` | The optimizer outputs for the study step; the subfolder name encodes the pgen parameters (e.g. `HEALS.200.MELEE.true.MP.6.OBJ.elements`). |
| `.../report.txt` | One block per candidate set: fitness, damage, targeted stats, characteristics, items and chromosome. |
| `.../summary.csv` | All stat totals side by side, one column per candidate. |
| `.../pca.png` | PCA of the candidates' stats, colored by fitness. |
| `.../generations.png` | Best fitness per generation for each island (convergence check). |
| `.../config.json` | Fully resolved optimizer configuration (stat IDs instead of names). |
| `.../*.out`, `*.err` | stdout/stderr of the step. |
| `meta/`, `logs/`, `status.csv`, `batch.info`, `*.pkl` | Maestro bookkeeping. The top-level `report-<name>.txt` files are empty Maestro placeholders, not the optimizer report. |

The optimizer's results are in `report.txt`. When the spec sets a `REFERENCE`, `Solution 0` is that reference set and the optimizer's candidates follow it; otherwise every solution is a candidate. Solutions are not sorted by fitness, so check the `Fitness:` lines (or the `summary.csv`) to find the best ones.

## int-heals

[`workflow.steamer.yaml`](int-heals/workflow.steamer.yaml) + [`pgen.steamer.py`](int-heals/pgen.steamer.py)

**Use case:** a damage build that is also required to keep a minimum heal bonus. The objective is spell damage (`elements`) in Intelligence only, and `HEALS: 200` adds a lower-bound target on the flat Heals bonus, so sets with less than 200 Heals are penalized. This is the "require a minimum heal bonus" pattern described in [workflows/README.md](../workflows/README.md#heal-optimization).

- Melee and ranged weapons allowed; 12 AP, 6 MP, 6 range, 3800 vit, 10–13% resistances.
- Forced items: Dofus Ocre (7754), Dofus Vulbis (6980), Martillo poseído (25222) and Amor de Helsefina (32118). Meriana (32121) and 13344 are excluded.
- Exos: AP, MP, range and 200 vit.

**Result** ([report.txt](int-heals/run_optimization/HEALS.200.MELEE.true.MP.6.OBJ.elements/report.txt)): 99 unpenalized candidates. The best (Solutions 0 and 1) reach 1858 spell damage with 1411 Intelligence, 207 Heals (433 healing on the reference heal), 4500 vit and every target met.

## long-range-multi-crit

[`workflow.cra.yaml`](long-range-multi-crit/workflow.cra.yaml) + [`pgen.cra.py`](long-range-multi-crit/pgen.cra.py)

**Use case:** a 4-element (agi int str cha) ranged spell caster that needs high crit, compared against an existing set. `CRIT: 87` is both a target and switches on crit weighting in the damage formula. The pgen has a commented-out list of 2-element combinations to sweep; this run used only the omni-element entry.

- Ranged only, weapon range ≥ 6; 12 AP, 5 MP, 6 range, 3800 vit, 10–13% resistances.
- Forced items: Dofus Ocre (7754), Dofus Abisal (18043), Dofus Turquesa (739).
- Exos: AP, MP, 2% crit, range and 200 vit.
- `REFERENCE` is an existing set to compare against (Miauvizor / Vueloceronte pieces).

**Result** ([report.txt](long-range-multi-crit/run_optimization/ELE.agi_int_str_cha.MP.5.OBJ.elements/report.txt)): the reference (Solution 0) scores 2040. The best candidate (Solution 1) scores 2221 (+9%) with an Estrígido / Tentenhuevo / Noai Aludem mix, 93% crit, +105 power and the same AP/MP/range, at the cost of lower resistances (15–33%) that still clear the targets.

## tank-lock

[`sacri-tank.yaml`](tank-lock/sacri-tank.yaml)

**Use case:** a melee Agility tank that maximizes weapon life-steal damage per AP (`steal` + `NORMALIZE_BY_APCOST`) while hitting many defensive targets at once: 4000 vit, 20% in every resistance, 150 lock, 60 dodge and 3200 initiative.

- Melee only; 12 AP, 5 MP.
- Forced items: Dofus Ocre (7754), Dofus Marfil (7115), Dofus Abisal (18043), Tintarela picuda (24034) and Valentía de la Señorita Jhessica (20366).
- Exos: AP, MP and 200 vit.
- `REFERENCE` is an existing set to compare against.

**Result** ([report.txt](tank-lock/run_training/report.txt)): the reference scores 833 steal damage. The best candidates (Solutions 1 and 2) reach 852 while raising initiative from 3531 to 4001 and lock from 150 to 155, swapping in Martillelo amulet, Botón de Psikopomzopato and a pet. The gain is small, which suggests the reference was already close to optimal given the forced items.

This example comes from an older version of the spec: its step is named `run_training` and it calls `$(REPO_ROOT)/main.py` instead of `scripts/main.py`, so it will not run as-is. Use [workflows/workflow.sacri-tank.yaml](../workflows/workflow.sacri-tank.yaml) to reproduce it.

## Re-running an example

The specs set `REPO_ROOT: $(SPECROOT)/..`, so they need to sit in `workflows/` to find `scripts/main.py`. Run the original specs from there:

```bash
cd workflows
maestro run -p pgen.steamer.py workflow.steamer.yaml   # int-heals
maestro run -p pgen.cra.py workflow.cra.yaml           # long-range-multi-crit
maestro run workflow.sacri-tank.yaml                   # tank-lock
```

The GA is stochastic, so new runs find similar but not identical sets.
