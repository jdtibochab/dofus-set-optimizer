# Examples

Three finished Maestro runs, kept here so you can see what the optimizer produces without running it. Each folder is a complete Maestro workspace (spec, parameter generator, logs and optimizer outputs) copied from `workflows/report-<name>_<timestamp>/`. Folders are named after the build (role and element), not the class, since the specs don't pass `--class`.

All three are level 200, fully scrolled characters at 12 AP with 16 islands × 300 generations, using the in-game characteristic point costs (e.g. 398 points in a single element, 174 in each of four). Reports are in Spanish (`LANGUAGE: "es"`), so stats show up as e.g. `PA` (AP), `PM` (MP), `vitalidad`, `placaje` (lock), `huida` (dodge) and `de cura` (Heals).

| Example | Build | Objective | Key targets | Reference set | Best fitness |
| --- | --- | --- | --- | --- | --- |
| [heals-int](#heals-int) | Intelligence hybrid | `elements` | 6 MP, 6 range, ≥ 200 Heals | none | 1876 |
| [ranged-multi-crit](#ranged-multi-crit) | 4-element ranged crit | `elements` | 5 MP, 6 range, 87% crit | yes (2049) | 2077 |
| [tank-agi](#tank-agi) | Agility melee tank | `steal` / AP | 5 MP, 4000 vit, 20% res, 150 lock, 60 dodge, 3200 initiative | yes (851) | 864 |

## Folder layout

| Path | Content |
| --- | --- |
| `workflow.<name>.yaml` | The exact Maestro spec used for the run. The copy in [workflows/](../workflows/) has since gained an `html_report` step that builds the reports and study index automatically. |
| `pgen.<name>.py` | Parameter generator that fills `$(OBJECTIVE)`, `$(MP)`, etc. (not used by tank-agi). |
| `run_optimization/<params>/` | The optimizer outputs. With a pgen, the subfolder name encodes its parameters (e.g. `HEALS.200.MELEE.true.MP.6.OBJ.elements`); tank-agi has no pgen, so its outputs sit directly in `run_optimization/`. |
| `.../report.html` | The report to start with: setup, a list of all candidate sets with the best one marked (click a row to see its items and stats), and a table comparing every set's damage, healing and targets. Each set has an "Open in Dofus Forge" link. Open it in a browser. |
| `.../report.txt` | One block per candidate set: fitness, damage, targeted stats, characteristics, items, chromosome and Dofus Forge link. |
| `.../summary.csv` | All stat totals side by side, one column per candidate. |
| `.../pca.png` | PCA of the candidates' stats, colored by fitness. |
| `.../generations.png` | Best fitness per generation for each island (convergence check). |
| `.../config.json` | Fully resolved optimizer configuration (stat IDs instead of names). |
| `.../*.out`, `*.err` | stdout/stderr of the step. |
| `meta/`, `logs/`, `status.csv`, `batch.info`, `*.pkl` | Maestro bookkeeping. The top-level `report-<name>.txt` files are empty Maestro placeholders, not the optimizer report. |

When the spec sets a `REFERENCE`, `Solution 0` (`Reference` in `report.html`) is that reference set and the optimizer's candidates follow it; otherwise every solution is a candidate.

### Dofus Forge links

The specs don't pass `--class`, so the links open in Dofus Forge with no class selected: pick one there to see stat totals. To bake a class into the links, rebuild the report with it:

```bash
python scripts/html_report.py examples/tank-agi/run_optimization --class sacrier
```

Exos aren't part of Dofus Forge's link format, so add them there by hand.

## heals-int

[`workflow.steamer.yaml`](heals-int/workflow.steamer.yaml) + [`pgen.steamer.py`](heals-int/pgen.steamer.py)

**Use case:** a damage build that is also required to keep a minimum heal bonus. The objective is spell damage (`elements`) in Intelligence only, and `HEALS: 200` adds a lower-bound target on the flat Heals bonus, so sets with less than 200 Heals are penalized. This is the "require a minimum heal bonus" pattern described in [workflows/README.md](../workflows/README.md#heal-optimization).

- Melee and ranged weapons allowed; 12 AP, 6 MP, 6 range, 3800 vit, 10–13% resistances.
- Forced items: Dofus Ocre (7754), Dofus Vulbis (6980), Martillo poseído (25222) and Amor de Helsefina (32118). Meriana (32121) and 13344 are excluded.
- Exos: AP, MP, range and 200 vit.

**Result** ([report.html](heals-int/run_optimization/HEALS.200.MELEE.true.MP.6.OBJ.elements/report.html)): 134 unpenalized candidates. The best (Solution 0) reaches 1876 spell damage with 1478 Intelligence, 201 Heals (438 healing on the reference heal), 4150 vit and every target met, mixing secular hat and belt, Martillelo cape, Otomai flask and the Purple Dofus around the forced items.

## ranged-multi-crit

[`workflow.cra.yaml`](ranged-multi-crit/workflow.cra.yaml) + [`pgen.cra.py`](ranged-multi-crit/pgen.cra.py)

**Use case:** a 4-element (agi int str cha) ranged spell caster that needs high crit, compared against an existing set. `CRIT: 87` is both a target and switches on crit weighting in the damage formula. The pgen has a commented-out list of 2-element combinations to sweep; this run used only the omni-element entry.

- Ranged only, weapon range ≥ 6; 12 AP, 5 MP, 6 range, 3800 vit, 10–13% resistances.
- Forced items: Dofus Ocre (7754), Dofus Abisal (18043), Dofus Turquesa (739).
- Exos: AP, MP, 2% crit, range and 200 vit.
- `REFERENCE` is an existing set to compare against (Vueloceronte / Miauvizor pieces). It lists seven Dofus and trophies (six Dofus plus Potente mayor), one more than a character can equip, so its score is slightly flattering and its Dofus Forge link drops the seventh.

**Result** ([report.html](ranged-multi-crit/run_optimization/ELE.agi_int_str_cha.MP.5.OBJ.elements/report.html)): 67 candidates. The reference (Solution 0) scores 2049. The best candidate (Solution 1) scores 2077 (+1.4%) with an Estrígido / Kukoloide / Tal Kasha mix and Varita de Torkelonia: the same 89% crit, AP, MP and range, +110 power and +250 vit, at the cost of lower resistances (13–29% instead of 19–39%) that still clear the targets.

## tank-agi

[`workflow.sacri-tank.yaml`](tank-agi/workflow.sacri-tank.yaml)

**Use case:** a melee Agility tank that maximizes weapon life-steal damage per AP (`steal` + `NORMALIZE_BY_APCOST`) while hitting many defensive targets at once: 4000 vit, 20% in every resistance, 150 lock, 60 dodge and 3200 initiative.

- Melee only; 12 AP, 5 MP.
- Forced items: Dofus Ocre (7754), Dofus Marfil (7115), Dofus Abisal (18043), Tintarela picuda (24034) and Valentía de la Señorita Jhessica (20366). Meriana (32121), 20354 and 13344 are excluded.
- Exos: AP, MP and 200 vit.
- `REFERENCE` is an existing set to compare against.

**Result** ([report.html](tank-agi/run_optimization/report.html)): 171 candidates. The reference scores 851 steal damage. The best candidates (Solutions 1–3, tied) reach 864 (+1.5%) with 1403 Agility, swapping in Aletas de trithón, Capa de sota afortunada, Botón de Psikopomzopato, Casco de vueloceronte, a Mortiélago petsmount and Lozano mayor instead of the Purple Dofus. Initiative rises from 3573 to 3703, power from 180 to 220 and lock from 154 to 157, while dodge drops from 133 to 80 (still above the 60 target). The gain is small, which suggests the reference was already close to optimal given the forced items.

## Re-running an example

The specs set `REPO_ROOT: $(SPECROOT)/..`, so they need to sit in `workflows/` to find `scripts/main.py`. Run the copies there:

```bash
cd workflows
maestro run -p pgen.steamer.py workflow.steamer.yaml   # heals-int
maestro run -p pgen.cra.py workflow.cra.yaml           # ranged-multi-crit
maestro run workflow.sacri-tank.yaml                   # tank-agi
```

The GA is stochastic, so new runs find similar but not identical sets.
