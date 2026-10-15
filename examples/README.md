# Examples

Three finished Maestro studies, kept here so you can see what the optimizer produces without running it. Each folder is a complete Maestro workspace (spec, parameter generator, logs and optimizer outputs) copied from `workflows/report-<name>_<timestamp>/`. Two of them are parameter sweeps (four runs each) and one is a single run. Folders are named after the build (role and element), not the class, since the specs don't pass `--class`.

All three are level 200, fully scrolled characters at 12 AP with 16 islands × 300 generations, using the in-game characteristic point costs (e.g. 398 points in a single element, 174 in each of four). Reports are in Spanish (`LANGUAGE: "es"`), so stats show up as e.g. `PA` (AP), `PM` (MP), `vitalidad`, `placaje` (lock), `huida` (dodge) and `de cura` (Heals).

| Example | Build | Runs (swept parameters) | Key targets | Reference set | Best fitness |
| --- | --- | --- | --- | --- | --- |
| [healer](#healer) | Intelligence or Chance hybrid with a heal weapon | 4: `ELEMENTS` (`cha`, `int`) × `OBJECTIVE` (`elements`, `elements weapon-heals`) | 6 MP, 6 range, ≥ 200 Heals | none | 1832 / 2055 (`cha`), 1892 / 2211 (`int`) |
| [ranged-multi-crit](#ranged-multi-crit) | 4-element ranged crit | 4: `MP` (5, 6) × `OBJECTIVE` (`weapon`, `elements weapon`) | 5 or 6 MP, 6 range, 87% crit | yes | 316.6 / 2444.1 (5 MP), 326.8 / 2321.5 (6 MP) |
| [tank-agi](#tank-agi) | Agility melee tank | 1 | 5 MP, 4000 vit, 20% res, 150 lock, 60 dodge, 3200 initiative | yes (170.1) | 175.3 |

Fitness values aren't comparable across objectives: `weapon` and `steal` are per AP, and `elements weapon` adds the spell damage to the weapon damage per AP.

## Folder layout

| Path | Content |
| --- | --- |
| `index.html` | Study overview, built by the `html_report` step. For a sweep it has one row per run with its parameter values (instead of the long folder name), best fitness, targets met, best weapon and a link to the run's report. |
| `workflow.<name>.yaml` | The exact Maestro spec used for the study (identical to the one in [workflows/](../workflows/)). |
| `pgen.<name>.py` | Parameter generator that fills `$(OBJECTIVE)`, `$(MP)`, etc. (not used by tank-agi). |
| `run_optimization/<params>/` | The optimizer outputs. With a pgen, the subfolder name encodes the run's parameters (e.g. `ELEMENTS.int.HEALS.200.MELEE.true.MP.6.OBJ.elements_weapon-heals`, with spaces in values turned into underscores); tank-agi has no pgen, so its outputs sit directly in `run_optimization/`. |
| `html_report/` | Output of the `html_report` step, which rebuilds every run's `report.html` and writes `index.html`. |
| `.../report.html` | The report of a run, the page to start with: setup, a list of all candidate sets with the best one marked (click a row to see its items and stats), and a table comparing every set's damage, healing and targets. Each set has an "Open in Dofus Forge" link. Open it in a browser. |
| `.../report.txt` | One block per candidate set: fitness, damage, spell and weapon healing, targeted stats, characteristics, items, chromosome and Dofus Forge link. |
| `.../summary.csv` | All stat totals side by side, one column per candidate. |
| `.../pca.png` | PCA of the candidates' stats, colored by fitness. |
| `.../generations.png` | Best fitness per generation for each island (convergence check). |
| `.../config.json` | Fully resolved optimizer configuration (stat IDs instead of names). |
| `.../*.out`, `*.err` | stdout/stderr of the step. |
| `meta/`, `logs/`, `status.csv`, `batch.info`, `*.pkl` | Maestro bookkeeping. The top-level `report-<name>.txt` files are empty Maestro placeholders, not the optimizer report. |

When the spec sets a `REFERENCE`, `Solution 0` (`Reference` in `report.html`) is that reference set and the optimizer's candidates follow it; otherwise every solution is a candidate.

### Dofus Forge links

The specs don't pass `--class`, so the links open in Dofus Forge with no class selected: pick one there to see stat totals. To bake a class into the links, rebuild the report with it. For a sweep, pass the study folder to rebuild every run and the index:

```bash
python scripts/html_report.py examples/tank-agi/run_optimization --class sacrier
python scripts/html_report.py examples/healer --class foggernaut
```

Exos aren't part of Dofus Forge's link format, so add them there by hand.

## healer

[`workflow.steamer.yaml`](healer/workflow.steamer.yaml) + [`pgen.steamer.py`](healer/pgen.steamer.py)

**Use case:** a damage build that also needs a minimum heal bonus (`HEALS: 200`, so sets below 200 Heals are penalized), and what changes when the weapon heals too. The sweep runs the same character with Chance and with Intelligence, once maximizing spell damage (`elements`) and once adding the weapon's healing per AP (`elements weapon-heals`). `weapon-heals` scores every heal line of the weapon, scaled by the element's characteristic plus the Heals bonus; neutral heals, which most heal weapons have since 3.7, are assumed converted with a forgemagic éclat to the selected element (see [Objectives](../README.md#arguments) in the main README).

- Melee and ranged weapons allowed; 12 AP, 6 MP, 6 range, 3800 vit, 10–13% resistances.
- Forced items: Dofus Ocre (7754), Dofus Vulbis (6980) and Amor de Helsefina (32118). **No heal weapon is forced**: in the `weapon-heals` runs the optimizer finds one by itself. Meriana (32121) and 13344 are excluded.
- Exos: AP, MP, range and 200 vit.

**Results** (every best set meets all its targets; [`index.html`](healer/index.html) compares the runs):

| Elements | Objective | Candidates | Best fitness | Best weapon | Spell damage | Weapon healing | Heals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `cha` | `elements` | 122 | 1832 | Piramvarita | 1832 | — | 204 |
| `cha` | `elements weapon-heals` | 112 | 2055 | Martillo poseído (4 AP) | 1738 | 1267 (317 / AP) | 205 |
| `int` | `elements` | 124 | 1892 | Arco Honte | 1892 | — | 200 |
| `int` | `elements weapon-heals` | 173 | 2211 | Varita de Malefíscof (3 AP) | 1775 | 1309 (436 / AP) | 202 |

([`cha` report](healer/run_optimization/ELEMENTS.cha.HEALS.200.MELEE.true.MP.6.OBJ.elements_weapon-heals/report.html), [`int` report](healer/run_optimization/ELEMENTS.int.HEALS.200.MELEE.true.MP.6.OBJ.elements_weapon-heals/report.html))

- **Weapon healing changes the weapon.** The optimizer finds the Possessed Hammer unprompted: it is in 104 of the 112 `cha` candidates and 157 of the 173 `int` ones, with the Malléfisk Wand (Varita de Malefíscof) making up most of the rest. Without `weapon-heals` the weapon is just whichever one boosts spell damage (Piramvarita, Arco Honte).
- **The trade is spell damage for healing:** spell damage drops by 94 (−5.1%) for `cha` and 117 (−6.2%) for `int`, and the sets heal 1267–1309 per hit in exchange. The Heals target (≥ 200) is met either way.
- **Intelligence ends ahead of Chance in both objectives** (1892 vs 1832, and 2211 vs 2055).
- `weapon-heals` scores one hit per AP, so the Possessed Hammer's two casts per turn aren't counted.

## ranged-multi-crit

[`workflow.cra.yaml`](ranged-multi-crit/workflow.cra.yaml) + [`pgen.cra.py`](ranged-multi-crit/pgen.cra.py)

**Use case:** a 4-element (agi int str cha) ranged caster that needs high crit, compared against an existing set. `CRIT: 87` is both a target and switches on crit weighting in the damage formula. The sweep crosses 5 and 6 MP with two objectives: the weapon alone (`weapon`, per AP) and the weapon plus a generic spell (`elements weapon`). The pgen has a commented-out list of 2-element combinations to sweep; this study used only the omni-element entry.

- Ranged only, weapon range ≥ 6; 12 AP, 5 or 6 MP, 6 range, 3800 vit, 10–13% resistances.
- Forced items: Dofus Ocre (7754), Dofus Abisal (18043), Dofus Turquesa (739).
- Exos: AP, MP, 2% crit, range and 200 vit.
- `REFERENCE` is an existing set to compare against (Vueloceronte / Miauvizor pieces, 89% crit, 5 MP). It lists seven Dofus and trophies (six Dofus plus Potente mayor), one more than a character can equip, so its score is slightly flattering and its Dofus Forge link drops the seventh. In the 6 MP runs the reference misses the MP target, so its fitness is penalized there.

**Results** (reference vs best candidate; [`index.html`](ranged-multi-crit/index.html) compares the runs):

| MP | Objective | Candidates | Reference | Best | Change | Best set |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | `weapon` | 38 | 308.5 | 316.6 | +2.6% | Arco de vueloceronte, Noai Aludem and Rhoarim pieces |
| 5 | `elements weapon` | 36 | 2357.9 | 2444.1 | +3.7% | Arco de vueloceronte, kukoloide and Tal Kasha pieces, 2106 spell damage |
| 6 | `weapon` | 7 | 255.0 (308.5 before the MP penalty) | 326.8 | +5.9% vs the unpenalized reference | Arco de vueloceronte, Golosorak and Noai Aludem pieces |
| 6 | `elements weapon` | 20 | 1948.8 (2357.9 before the MP penalty) | 2321.5 | −1.5% vs the unpenalized reference | Arco de vueloceronte, Golosorak and Noai Aludem pieces, 1998 spell damage |

([5 MP `weapon`](ranged-multi-crit/run_optimization/ELE.agi_int_str_cha.MP.5.OBJ.weapon/report.html), [5 MP `elements weapon`](ranged-multi-crit/run_optimization/ELE.agi_int_str_cha.MP.5.OBJ.elements_weapon/report.html), [6 MP `weapon`](ranged-multi-crit/run_optimization/ELE.agi_int_str_cha.MP.6.OBJ.weapon/report.html), [6 MP `elements weapon`](ranged-multi-crit/run_optimization/ELE.agi_int_str_cha.MP.6.OBJ.elements_weapon/report.html))

- **Every best set keeps the Arco de vueloceronte** and meets all its targets (87–90% crit, 6 range, 12 AP and the 3800+ vit).
- **The 6th MP costs a little once spell damage counts.** For the weapon alone, the best 6 MP set beats the 5 MP reference by 5.9%. With spell damage added, the best 6 MP set ends 1.5% below the reference's raw score (and 5.0% below the best 5 MP set); it has 190 power against 270 in the reference.
- **The 5 MP `weapon` run didn't find the best set.** Every 6 MP set also meets the 5 MP target, so the 5 MP optimum can't be lower than 326.8, yet that run's best is 316.6. The search is stochastic and doesn't guarantee the optimum; running more islands or generations, or re-running, may close the gap.
- **Fewer candidates at 6 MP** (7 and 20, against 38 and 36): fewer unpenalized sets were found once the MP target was raised.

## tank-agi

[`workflow.sacri-tank.yaml`](tank-agi/workflow.sacri-tank.yaml)

**Use case:** a melee Agility tank that maximizes weapon life-steal damage per AP (`steal` + `NORMALIZE_BY_APCOST`) while hitting many defensive targets at once: 4000 vit, 20% in every resistance, 150 lock, 60 dodge and 3200 initiative.

- Melee only; 12 AP, 5 MP.
- Forced items: Dofus Ocre (7754), Dofus Marfil (7115), Dofus Abisal (18043) and Valentía de la Señorita Jhessica (20366). **The scythe is no longer forced**: the optimizer still picks Tintarela picuda (24034) in all 108 candidates. Meriana (32121), 20354 and 13344 are excluded.
- Exos: AP, MP and 200 vit.
- `REFERENCE` is an existing set to compare against.

**Result** ([report.html](tank-agi/run_optimization/report.html)): 108 candidates. The reference scores 170.1 steal damage per AP (851 per hit). The best candidate (Solution 1) scores 175.3 (876 per hit, +3.0%), clearly ahead of the next best (172.3, tied across several sets). It differs from the reference in 8 items and doesn't use the Purple Dofus: Alianza golosona, Aletas de trithón, Capa de sota afortunada, Escudo Mónimo, Diadema de Ganymed, a Dragopavo almendrado y ébano and Lozano mayor. Power rises from 180 to 300, vitality from 4250 to 4700 and lock from 154 to 162, at the cost of lower dodge (133 to 112) and initiative (3573 to 3438), both still above their targets. Agility drops slightly (1443 to 1408).

## Re-running an example

The specs set `REPO_ROOT: $(SPECROOT)/..`, so they need to sit in `workflows/` to find `scripts/main.py`. Run the copies there:

```bash
cd workflows
maestro run -p pgen.steamer.py workflow.steamer.yaml   # healer
maestro run -p pgen.cra.py workflow.cra.yaml           # ranged-multi-crit
maestro run workflow.sacri-tank.yaml                   # tank-agi
```

The GA is stochastic, so new runs find similar but not identical sets. Each study ends with the `html_report` step, so `index.html` appears in the study folder without further commands.
