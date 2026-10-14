"""
Render optimization results as self-contained HTML reports.

Every run writes report.html next to report.txt. To (re)build reports for
existing runs, pass run directories, or a Maestro study directory to render
every run below it plus an index.html comparing them:

    python scripts/html_report.py reports/2026-10-08_10-00-00
    python scripts/html_report.py workflows/report-cra_20261008-175406
"""
import argparse
import html
import json
import os
import re
from datetime import datetime

import yaml

from dofus_forge import CLASSES as DOFUS_FORGE_CLASSES, chromosome_url
from utils import get_set_contribution

# Stats shown in the key stats grid, in display order
_KEY_STATS = [12, 8, 31, 9, 10, 32, 29, 24, 26, 59]
_CHARACTERISTICS = [45, 13, 22, 36]  # Strength, Intelligence, Chance, Agility
_RESISTANCES = [34, 63, 37, 17, 16]  # Neutral, Earth, Fire, Water, Air
# On-hit weapon effects and the set bonus counter, hidden from stat tables
_HIDDEN_STATS = {179, 225, 238, 72}

_HARD_PENALTIES = {
    "duplicated_dofus_or_trophy": "Duplicated Dofus or trophy",
    "duplicated_rings": "Duplicated rings",
}

_OBJECTIVE_LABELS = {
    "weapon": "Weapon damage",
    "elements": "Spell damage",
    "steal": "Steal damage",
    "push": "Push damage",
    "heals": "Healing",
}

_CSS = """
:root {
  --bg: #f6f6f3; --surface: #ffffff; --surface-2: #f0f0ec; --text: #1d1d1b;
  --muted: #68685f; --border: #e2e2dc; --accent: #3451b2; --accent-bg: #e8ecfa;
  --ok: #217a3c; --ok-bg: #e3f3e8; --warn: #9a5800; --warn-bg: #fdf0dc;
  --bad: #b42323; --bad-bg: #fbe7e7;
  --z-hi: #2a78d6; --z-lo: #e34948;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #141413; --surface: #1d1d1b; --surface-2: #262623; --text: #ecece6;
    --muted: #a0a097; --border: #34342f; --accent: #8fa6ff; --accent-bg: #232a45;
    --ok: #6fcf8d; --ok-bg: #18301f; --warn: #f0b45c; --warn-bg: #352812;
    --bad: #f28b8b; --bad-bg: #3a1c1c;
    --z-hi: #3987e5; --z-lo: #e66767;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 14px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
main { max-width: 1200px; margin: 0 auto; padding: 24px 16px 64px; }
h1 { font-size: 24px; margin: 0 0 4px; letter-spacing: -0.01em; }
h2 { font-size: 17px; margin: 32px 0 12px; }
h3 { font-size: 13px; margin: 0 0 8px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.muted { color: var(--muted); }
.num { font-variant-numeric: tabular-nums; text-align: right; white-space: nowrap; }
.small { font-size: 12px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 12px 0 0; }
.chip {
  display: inline-flex; align-items: center; gap: 4px; padding: 2px 10px;
  border-radius: 999px; background: var(--surface-2); border: 1px solid var(--border);
  font-size: 12px; white-space: nowrap;
}
.chip.accent { background: var(--accent-bg); border-color: transparent; color: var(--accent); font-weight: 600; }
.badge {
  display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 12px;
  font-weight: 600; white-space: nowrap;
}
.badge.ok { background: var(--ok-bg); color: var(--ok); }
.badge.warn { background: var(--warn-bg); color: var(--warn); }
.badge.bad { background: var(--bad-bg); color: var(--bad); }
.badge.ref { background: var(--accent-bg); color: var(--accent); }
.badge.best { background: var(--text); color: var(--bg); }
.grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
.scroll { overflow-x: auto; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; }
table { border-collapse: collapse; width: 100%; }
th, td { padding: 6px 10px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: middle; }
th { font-size: 12px; color: var(--muted); font-weight: 600; background: var(--surface-2); white-space: nowrap; }
tr:last-child td { border-bottom: none; }
.card table th { background: none; padding-left: 0; }
.card table td { padding-left: 0; }
th.stat-name, td.stat-name { white-space: nowrap; position: sticky; left: 0; background: var(--surface); z-index: 1; }
th.stat-name { background: var(--surface-2); }
td.ok { color: var(--ok); background: var(--ok-bg); }
td.bad { color: var(--bad); background: var(--bad-bg); font-weight: 600; }
td.top { font-weight: 700; }
td.met-ok { color: var(--ok); font-weight: 600; }
td.met-bad { color: var(--bad); font-weight: 600; }
td.z-hi-1 { background: color-mix(in srgb, var(--z-hi) 14%, transparent); }
td.z-hi-2 { background: color-mix(in srgb, var(--z-hi) 30%, transparent); }
td.z-hi-3 { background: color-mix(in srgb, var(--z-hi) 50%, transparent); }
td.z-lo-1 { background: color-mix(in srgb, var(--z-lo) 14%, transparent); }
td.z-lo-2 { background: color-mix(in srgb, var(--z-lo) 30%, transparent); }
td.z-lo-3 { background: color-mix(in srgb, var(--z-lo) 50%, transparent); }
.miss { color: var(--bad); font-weight: 700; }
.pass { color: var(--muted); }
.z-legend { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 14px; margin: 0 0 10px; }
.z-legend .swatch { display: inline-block; width: 22px; height: 14px; border-radius: 3px; vertical-align: -2px; margin-right: 4px; border: 1px solid var(--border); }
tr.objective td.stat-name, tr.objective td.top { color: var(--accent); }
tr.objective td.stat-name { font-weight: 600; }
tr.group-end td { border-bottom: 2px solid var(--muted); }
.icon { width: 32px; height: 32px; object-fit: contain; display: block; }
.sol-list { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.sol-row {
  display: grid; grid-template-columns: var(--sol-cols); gap: 12px; align-items: center;
  padding: 8px 14px; border-bottom: 1px solid var(--border);
}
.sol-row > .num { text-align: right; font-variant-numeric: tabular-nums; }
.sol-row > .met-ok { color: var(--ok); font-weight: 600; }
.sol-row > .met-bad { color: var(--bad); font-weight: 600; }
.sol-head { font-size: 12px; color: var(--muted); font-weight: 600; background: var(--surface-2); }
details.solution:last-child > summary { border-bottom: none; }
details.solution > summary { list-style: none; cursor: pointer; }
details.solution > summary:hover { background: var(--surface-2); }
details.solution > summary::-webkit-details-marker { display: none; }
.sol-label { font-weight: 600; white-space: nowrap; }
.sol-label::before { content: "▸"; color: var(--muted); display: inline-block; width: 1.1em; }
details.solution[open] .sol-label::before { content: "▾"; }
details.solution.is-best > summary { font-weight: 600; }
details.solution[open] { box-shadow: inset 3px 0 0 var(--accent); }
details.solution[open] > summary { background: var(--accent-bg); }
.sol-body { padding: 16px; display: grid; gap: 16px; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
  border-bottom: 1px solid var(--border); background: var(--bg); }
details.solution:last-child .sol-body { border-bottom: none; }
@media (max-width: 860px) {
  .sol-body { grid-template-columns: minmax(0, 1fr); }
  .sol-row { display: flex; flex-wrap: wrap; gap: 4px 14px; }
  .sol-row.sol-head { display: none; }
  .sol-row > .num { text-align: left; }
  .sol-row [data-label]::before { content: attr(data-label) ": "; color: var(--muted); font-size: 12px; font-weight: 400; }
}
@media (max-width: 600px) { .wide-only { display: none; } }
.fitness { font-weight: 700; font-variant-numeric: tabular-nums; }
.stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 8px; }
.stat { background: var(--surface-2); border-radius: 6px; padding: 6px 10px; }
.stat .label { font-size: 11px; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stat .value { font-size: 16px; font-weight: 600; font-variant-numeric: tabular-nums; }
.stat.highlight { background: var(--accent-bg); }
.stat.highlight .value { color: var(--accent); }
.diff td:first-child { box-shadow: inset 3px 0 0 var(--warn); }
.issues { margin: 0; padding-left: 18px; color: var(--bad); }
details.more summary { cursor: pointer; color: var(--accent); font-size: 13px; margin-top: 4px; }
code.ids { display: block; white-space: pre-wrap; word-break: break-word; background: var(--surface-2); padding: 8px; border-radius: 6px; font-size: 12px; }
.plots { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }
.plots img { width: 100%; height: auto; background: #fff; border-radius: 6px; }
.stack > * + * { margin-top: 16px; }
a.ext { float: right; font-size: 13px; font-weight: 500; }
"""


def _esc(value):
    return html.escape(str(value), quote=True)


def _fmt(value):
    if value is None:
        return "—"
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.1f}"
    return f"{int(round(value)):,}"


def _signed(value):
    text = _fmt(abs(value))
    return f"+{text}" if value >= 0 else f"−{text}"


class _Context:
    """Run-wide lookups shared by every solution."""

    def __init__(self, optimizer):
        self.optimizer = optimizer
        self.config = optimizer.config
        self.language = self.config.get("language", "en")
        self.descriptions = optimizer.effect_descriptions
        self.objectives = self.config["objective"]
        if not isinstance(self.objectives, list):
            self.objectives = [self.objectives]
        self.requirements = []
        for bound_type, preferences in self.config.get("preferences", {}).items():
            for stat, preference in preferences.items():
                self.requirements.append((bound_type, int(stat), preference["target"]))
        self.inclusions = set(self.config.get("inclusions", {}).get("items", []))
        self.elements = list(optimizer.character.config.get("elements", []))

    def stat_label(self, stat):
        return self.descriptions.get(stat, {}).get(self.language) or f"Stat {stat}"

    def name(self, obj):
        return obj["name"].get(self.language) or obj["name"].get("en", "?")

    def objective_label(self, objective):
        label = _OBJECTIVE_LABELS.get(objective, self.stat_label(objective) if isinstance(objective, int) else str(objective))
        if objective in ("weapon", "steal") and self.config.get("normalize_by_apcost", True):
            label += " / AP"
        return label


def _solution_data(chromosome, ctx):
    """Collect everything the report shows for one solution."""
    totals = chromosome.totals
    requirements = []
    for bound_type, stat, target in ctx.requirements:
        actual = totals.get(stat, 0)
        met = actual >= target if bound_type == "lower" else actual <= target
        requirements.append({"stat": stat, "bound": bound_type, "target": target, "actual": actual, "met": met})

    issues = []
    for penalty in chromosome.penalties:
        kind = penalty["bound_type"]
        if kind in _HARD_PENALTIES:
            issues.append(_HARD_PENALTIES[kind])
        elif kind.startswith("item_conditions_not_met"):
            item = ctx.optimizer.items.get(int(kind.split(":")[1]))
            issues.append(f"Equip conditions not met: {ctx.name(item) if item else kind}")

    unmet = sum(not r["met"] for r in requirements)
    if issues:
        status = ("bad", "Invalid set")
    elif unmet:
        status = ("warn", f"{unmet} target{'s' if unmet > 1 else ''} missed")
    else:
        status = ("ok", "All targets met")

    ids = [i["ankama_id"] for i in chromosome.items]
    sets = []
    seen = set()
    for item in chromosome.items:
        if not item.get("hasParentSet"):
            continue
        set_id = item["parentSet"]["id"]
        item_set = ctx.optimizer.item_sets.get(set_id)
        if item_set is None or set_id in seen:
            continue
        seen.add(set_id)
        worn = len(set(ids) & set(item_set["items"]))
        bonus = {}
        if isinstance(item_set.get("effects"), dict):
            bonus = {k: v for k, v in get_set_contribution(item_set, worn).items()
                     if k not in _HIDDEN_STATS and v}
        sets.append({"name": ctx.name(item_set), "worn": worn, "total": len(item_set["items"]), "bonus": bonus})
    sets.sort(key=lambda s: (-s["worn"], s["name"]))

    scores = chromosome.get_objective_scores()
    weapon = chromosome.weapon
    return {
        "chromosome": chromosome,
        "ids": ids,
        "dofus_forge": chromosome_url(chromosome),
        "fitness": chromosome.fitness,
        "scores": scores if isinstance(scores, dict) else {},
        "metrics": [
            ("Weapon damage", chromosome.get_final_damage(type="weapon"), "weapon"),
            ("Spell damage", chromosome.get_final_damage(type="elements"), "elements"),
            ("Push damage", chromosome.get_push_damage(), "push"),
            ("Healing", chromosome.get_healing(), "heals"),
        ],
        "weapon": weapon,
        "requirements": requirements,
        "issues": issues,
        "status": status,
        "sets": sets,
    }


def _render_header(ctx, title, solutions, has_reference):
    config = ctx.config
    character = ctx.optimizer.character
    melee = character.config.get("melee")
    ranged = character.config.get("ranged")
    weapon_rule = " + ".join(
        [label for label, on in (("melee", melee), ("ranged", ranged)) if on]) or "any weapon"
    if ranged and not isinstance(ranged, bool):
        weapon_rule += f", range ≥ {ranged}"

    chips = [f'<span class="chip accent">Maximize: {_esc(" + ".join(ctx.objective_label(o) for o in ctx.objectives))}</span>']
    if character.config.get("class"):
        chips.append(f'<span class="chip">{_esc(character.config["class"].capitalize())}</span>')
    chips.append(f'<span class="chip">Level {character.level}</span>')
    chips.append(f'<span class="chip">Elements: {_esc(", ".join(ctx.stat_label(e) for e in ctx.elements))}</span>')
    chips.append(f'<span class="chip">Weapon: {_esc(weapon_rule)}</span>')
    if character.scrolled:
        chips.append('<span class="chip">Scrolled</span>')
    if character.exo:
        exo = ", ".join(f"{ctx.stat_label(int(k))} +{v}" for k, v in character.exo.items())
        chips.append(f'<span class="chip">Exos: {_esc(exo)}</span>')
    candidates = len(solutions) - (1 if has_reference else 0)
    chips.append(f'<span class="chip">{candidates} candidate set{"s" if candidates != 1 else ""}</span>')

    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""
<header>
  <h1>{_esc(title)}</h1>
  <div class="muted small">{_esc(config.get("path", ""))} · generated {generated}</div>
  <div class="chips">{"".join(chips)}</div>
</header>"""


def _item_list(ids, ctx):
    from data import items as all_items
    names = []
    for i in ids:
        # Excluded items are no longer in the optimizer's pool
        item = ctx.optimizer.items.get(i) or all_items.get(i)
        names.append(f"{_esc(ctx.name(item))} <span class=\"muted\">({i})</span>" if item else str(i))
    return ", ".join(names) or '<span class="muted">none</span>'


def _render_setup(ctx):
    rows = "".join(
        f"<tr><td>{_esc(ctx.stat_label(stat))}</td><td class=\"num\">{'≥' if bound == 'lower' else '≤'} {_fmt(target)}</td></tr>"
        for bound, stat, target in ctx.requirements)
    if not rows:
        rows = '<tr><td class="muted">No stat targets</td><td></td></tr>'

    objectives = "".join(f"<li>{_esc(ctx.objective_label(o))}</li>" for o in ctx.objectives)
    combined = "Scores are summed, then multiplied by the target penalties." if len(ctx.objectives) > 1 else \
        "The score is multiplied by the target penalties."

    config = ctx.config
    exclusions = [i for i in config.get("exclusions", {}).get("items", [])]
    ga = [("Islands", config.get("islands")), ("Generations", config.get("num_generations")),
          ("Population", config.get("population_size")), ("Parents mating", config.get("num_parents_mating")),
          ("Mutation", f"{config.get('mutation_type')} {config.get('mutation_rate')}"),
          ("Crossover", f"{config.get('crossover_type')} {config.get('crossover_rate')}"),
          ("Elitism", config.get("keep_elitism")), ("Level offset", config.get("level_offset"))]
    ga_rows = "".join(f"<tr><td>{_esc(k)}</td><td class=\"num\">{_esc(v)}</td></tr>" for k, v in ga)

    return f"""
<h2>Setup</h2>
<div class="grid">
  <div class="card"><h3>Objective</h3><ul>{objectives}</ul><p class="muted small">{combined}</p></div>
  <div class="card"><h3>Requirements</h3><table>{rows}</table></div>
  <div class="card stack">
    <div><h3>Forced items</h3><div class="small">{_item_list(sorted(ctx.inclusions), ctx)}</div></div>
    <div><h3>Excluded items</h3><div class="small">{_item_list(exclusions, ctx)}</div></div>
    <details class="more"><summary>Genetic algorithm settings</summary><table>{ga_rows}</table></details>
  </div>
</div>"""


def _label(index, has_reference):
    if has_reference:
        return "Reference" if index == 0 else f"#{index}"
    return f"#{index + 1}"


def _badges(idx, d, has_reference, best):
    # Target status is shown by the colored "Targets met" value; only invalid sets get a badge
    cls, text = d["status"]
    badges = f'<span class="badge {cls}">{_esc(text)}</span>' if cls == "bad" else ""
    if has_reference and idx == 0:
        badges += ' <span class="badge ref">Reference</span>'
    if idx == best:
        badges += ' <span class="badge best">Best</span>'
    return badges


def _render_solutions(data, ctx, has_reference, best):
    """One expandable row per set: the summary line holds the comparison columns, the body the details."""
    best_ids = set(data[best]["ids"]) if best is not None else None
    columns = ["5.5rem", "minmax(9rem, auto)", "5.5rem"] + ["6.5rem"] * len(ctx.objectives) + \
        ["minmax(8rem, 1fr)", "minmax(10rem, 1.6fr)", "4.5rem", "4.5rem", "4.5rem"]
    score_heads = "".join(f'<span class="num">{_esc(ctx.objective_label(o))}</span>' for o in ctx.objectives)
    rows = "".join(_render_solution(i, d, ctx, has_reference, best,
                                    None if i == best else best_ids, data)
                   for i, d in enumerate(data))
    return f"""
<h2>Solutions</h2>
<p class="muted small">Click a set to see its items, set bonuses and stats.</p>
<div class="sol-list" style="--sol-cols: {' '.join(columns)}">
  <div class="sol-row sol-head"><span>Set</span><span>Status</span><span class="num">Fitness</span>{score_heads}
    <span>Weapon</span><span>Set bonuses (≥ 2 pieces)</span><span class="num">Targets met</span>
    <span class="num">Items ≠ best</span><span>Dofus Forge</span></div>
  {rows}
</div>
<script>
function openTarget() {{
  var el = document.getElementById(location.hash.slice(1));
  if (el && el.tagName === "DETAILS") el.open = true;
}}
addEventListener("hashchange", openTarget);
openTarget();
</script>"""


def _z_scores(values, higher_is_better=True):
    """Signed z-score of each value within its row, positive meaning better; None when the row doesn't vary."""
    nums = [v for v in values if v is not None]
    if len(nums) < 2:
        return [None] * len(values)
    mean = sum(nums) / len(nums)
    std = (sum((v - mean) ** 2 for v in nums) / len(nums)) ** 0.5
    if not std:
        return [None] * len(values)
    sign = 1 if higher_is_better else -1
    return [None if v is None else sign * (v - mean) / std for v in values]


def _z_class(z):
    # Three equal steps per arm; |z| < 0.5 stays neutral
    if z is None or abs(z) < 0.5:
        return ""
    step = 3 if abs(z) >= 2 else 2 if abs(z) >= 1 else 1
    return f" z-{'hi' if z > 0 else 'lo'}-{step}"


def _z_title(z):
    return "" if z is None else f"z = {z:+.2f}"


def _render_requirements_matrix(data, ctx, has_reference):
    heads = "".join(f'<th class="num"><a href="#sol-{i}">{_label(i, has_reference)}</a></th>' for i in range(len(data)))
    rows = []

    # Damage and healing have no target: higher is better, and the highest value is bolded
    for m_idx, (label, _, key) in enumerate(data[0]["metrics"]):
        values = [d["metrics"][m_idx][1] for d in data]
        top = max(v for v in values if v is not None) if any(v is not None for v in values) else None
        cells = "".join(
            f'<td class="num{" top" if v == top and top else ""}{_z_class(z)}" title="{_z_title(z)}">{_fmt(v)}</td>'
            for v, z in zip(values, _z_scores(values)))
        objective = " objective" if key in ctx.objectives else ""
        rows.append(f'<tr class="metric{objective}"><td class="stat-name">{_esc(label)}</td>'
                    f'<td class="num muted">—</td>{cells}</tr>')
    cells = "".join(f'<td class="num">{d["weapon"]["apCost"]} / {d["weapon"]["maxCastPerTurn"]}</td>' if d["weapon"]
                    else '<td class="num muted">—</td>' for d in data)
    rows.append(f'<tr class="metric group-end"><td class="stat-name">Weapon AP / casts</td>'
                f'<td class="num muted">—</td>{cells}</tr>')

    # Requirements: colored by z-score in the direction of the bound, with ✓/✗ for the target
    for r_idx, (bound, stat, target) in enumerate(ctx.requirements):
        reqs = [d["requirements"][r_idx] for d in data]
        z_scores = _z_scores([r["actual"] for r in reqs], higher_is_better=bound == "lower")
        cells = []
        for r, z in zip(reqs, z_scores):
            mark = '<span class="pass">✓</span>' if r["met"] else '<span class="miss">✗</span>'
            title = f'{_signed(r["actual"] - target)} vs target' + (f' · {_z_title(z)}' if z is not None else "")
            cells.append(f'<td class="num{_z_class(z)}" title="{_esc(title)}">{mark} {_fmt(r["actual"])}</td>')
        rows.append(f"<tr><td class=\"stat-name\">{_esc(ctx.stat_label(stat))}</td>"
                    f"<td class=\"num muted\">{'≥' if bound == 'lower' else '≤'} {_fmt(target)}</td>{''.join(cells)}</tr>")
    legend = (
        '<div class="z-legend small muted">'
        '<span>Cell color compares each value with the other sets in its row (z-score):</span>'
        '<span><span class="swatch" style="background: color-mix(in srgb, var(--z-hi) 50%, transparent)"></span>'
        'better than average</span>'
        '<span><span class="swatch" style="background: color-mix(in srgb, var(--z-lo) 50%, transparent)"></span>'
        'worse than average</span>'
        '<span>darker = further from average (0.5, 1 and 2 standard deviations) · '
        '<span class="miss">✗</span> target missed · hover a cell for its z-score</span></div>')
    return f"""
<h2 id="by-solution">Damage and requirements by solution</h2>
{legend}
<div class="scroll"><table>
  <thead><tr><th class="stat-name">Stat</th><th class="num">Target</th>{heads}</tr></thead>
  <tbody>{"".join(rows)}</tbody>
</table></div>"""


def _render_solution(idx, d, ctx, has_reference, best, best_ids, data):
    chromosome = d["chromosome"]
    badges = _badges(idx, d, has_reference, best)
    weapon = _esc(ctx.name(d["weapon"])) if d["weapon"] else '<span class="muted">none</span>'
    scores = "".join(f'<span class="num" data-label="{_esc(ctx.objective_label(o))}">{_fmt(d["scores"].get(o))}</span>'
                     for o in ctx.objectives)
    met = sum(r["met"] for r in d["requirements"])
    met_cls = (" met-ok" if met == len(d["requirements"]) else " met-bad") if d["requirements"] else ""
    bonus_sets = ", ".join(f'{_esc(s["name"])} <span class="muted">{s["worn"]}/{s["total"]}</span>'
                           for s in d["sets"] if s["worn"] >= 2)
    diff = len(set(d["ids"]) ^ set(data[best]["ids"])) // 2 if best is not None else 0

    # Items in slot order
    item_rows = []
    for item in chromosome.items:
        item_set = ctx.optimizer.item_sets.get(item["parentSet"]["id"]) if item.get("hasParentSet") else None
        tags = []
        if item["ankama_id"] in ctx.inclusions:
            tags.append('<span class="badge ref">forced</span>')
        differs = best_ids is not None and item["ankama_id"] not in best_ids
        if differs:
            tags.append('<span class="badge warn">≠ best</span>')
        icon = f'<img class="icon" src="{_esc(item["image"])}" alt="" loading="lazy" onerror="this.style.visibility=\'hidden\'">' if item.get("image") else ""
        item_rows.append(f"""
<tr class="{'diff' if differs else ''}">
  <td>{icon}</td><td class="small muted">{_esc(item["type"]["name"].get(ctx.language, ""))}</td>
  <td>{_esc(ctx.name(item))} {" ".join(tags)}</td>
  <td class="small muted wide-only">{_esc(ctx.name(item_set)) if item_set else ""}</td>
  <td class="num small">{item["level"]}</td><td class="num small muted wide-only">{item["ankama_id"]}</td>
</tr>""")

    # Objectives and other damage numbers
    metric_cells = []
    for label, value, key in d["metrics"]:
        highlight = " highlight" if key in ctx.objectives else ""
        metric_cells.append(f'<div class="stat{highlight}"><div class="label">{_esc(label)}</div><div class="value">{_fmt(value)}</div></div>')
    if d["weapon"]:
        w = d["weapon"]
        metric_cells.append(f'<div class="stat"><div class="label">Weapon AP / casts</div><div class="value">{w["apCost"]} / {w["maxCastPerTurn"]}</div></div>')

    req_rows = "".join(
        f'<tr><td>{_esc(ctx.stat_label(r["stat"]))}</td>'
        f'<td class="num muted">{"≥" if r["bound"] == "lower" else "≤"} {_fmt(r["target"])}</td>'
        f'<td class="num {"ok" if r["met"] else "bad"}">{"✓" if r["met"] else "✗"} {_fmt(r["actual"])}</td>'
        f'<td class="num small muted">{_signed(r["actual"] - r["target"])}</td></tr>'
        for r in d["requirements"]) or '<tr><td class="muted">No stat targets</td></tr>'

    totals = chromosome.totals

    def stat_cells(stats, highlighted=()):
        return "".join(
            f'<div class="stat{" highlight" if s in highlighted else ""}"><div class="label" title="{_esc(ctx.stat_label(s))}">'
            f'{_esc(ctx.stat_label(s))}</div><div class="value">{_fmt(totals.get(s, 0))}</div></div>' for s in stats)

    set_rows = "".join(
        f'<tr><td>{_esc(s["name"])}</td><td class="num">{s["worn"]}/{s["total"]}</td>'
        f'<td class="small muted">{_esc(", ".join(f"{ctx.stat_label(k)} {_signed(v)}" for k, v in s["bonus"].items())) or "—"}</td></tr>'
        for s in d["sets"]) or '<tr><td class="muted">No set items</td></tr>'

    issues = ""
    if d["issues"]:
        issues = '<div class="card"><h3>Problems</h3><ul class="issues">' + \
            "".join(f"<li>{_esc(i)}</li>" for i in d["issues"]) + "</ul></div>"

    all_totals = "".join(
        f'<tr><td>{_esc(ctx.stat_label(k))}</td><td class="num small muted">{k}</td><td class="num">{_fmt(v)}</td></tr>'
        for k, v in sorted(totals.items(), key=lambda kv: ctx.stat_label(kv[0]))
        if k not in _HIDDEN_STATS and v)

    return f"""
<details class="solution{" is-best" if idx == best else ""}" id="sol-{idx}"{" open" if idx == best else ""}>
  <summary class="sol-row">
    <span class="sol-label">{_label(idx, has_reference)}</span><span>{badges}</span>
    <span class="num fitness" data-label="Fitness">{_fmt(d["fitness"])}</span>{scores}
    <span data-label="Weapon">{weapon}</span>
    <span class="small" data-label="Sets">{bonus_sets or '<span class="muted">—</span>'}</span>
    <span class="num{met_cls}" data-label="Targets met">{met}/{len(d["requirements"])}</span>
    <span class="num" data-label="Items ≠ best">{'—' if idx == best else diff}</span>
    <span><a href="{_esc(d["dofus_forge"])}" target="_blank" rel="noopener">Open ↗</a></span>
  </summary>
  <div class="sol-body">
    <div class="stack">
      <div class="card"><h3>Items <a class="ext" href="{_esc(d["dofus_forge"])}" target="_blank" rel="noopener">Open in Dofus Forge ↗</a></h3>
        <table>{"".join(item_rows)}</table></div>
      <div class="card"><h3>Sets</h3><table>{set_rows}</table></div>
    </div>
    <div class="stack">
      {issues}
      <div class="card"><h3>Damage and healing</h3><div class="stat-grid">{"".join(metric_cells)}</div></div>
      <div class="card"><h3>Requirements</h3><table>{req_rows}</table></div>
      <div class="card"><h3>Characteristics</h3><div class="stat-grid">{stat_cells(_CHARACTERISTICS, ctx.elements)}</div></div>
      <div class="card"><h3>Key stats</h3><div class="stat-grid">{stat_cells(_KEY_STATS)}</div>
        <h3 style="margin-top:12px">Resistances (%)</h3><div class="stat-grid">{stat_cells(_RESISTANCES)}</div>
        <details class="more"><summary>All stat totals</summary><table>{all_totals}</table></details>
        <details class="more"><summary>Item IDs (for --reference / --inclusions)</summary>
          <code class="ids">{" ".join(str(i) for i in d["ids"])}</code></details>
      </div>
    </div>
  </div>
</details>"""


def _render_plots(path):
    plots = [(name, label) for name, label in (("generations.png", "Best fitness per generation, per island"),
                                                ("pca.png", "PCA of candidate stat totals"))
             if os.path.exists(os.path.join(path, name))]
    if not plots:
        return ""
    figures = "".join(f'<figure class="card" style="margin:0"><h3>{_esc(label)}</h3><img src="{name}" alt="{_esc(label)}"></figure>'
                      for name, label in plots)
    return f'<h2>Convergence</h2><div class="plots">{figures}</div>'


def _page(title, body):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<style>{_CSS}</style>
</head>
<body><main>{body}</main></body>
</html>
"""


def build_report(optimizer, solutions, has_reference=False, title=None):
    """Return the report as (html, summary), where summary feeds the study index."""
    ctx = _Context(optimizer)
    path = ctx.config.get("path", "")
    title = title or os.path.basename(os.path.normpath(path)) or "Optimization report"
    data = [_solution_data(s, ctx) for s in solutions]

    candidates = [i for i in range(len(data)) if not (has_reference and i == 0)]
    best = max(candidates, key=lambda i: data[i]["fitness"]) if candidates else None

    if data:
        body = (_render_header(ctx, title, solutions, has_reference) + _render_setup(ctx)
                + _render_solutions(data, ctx, has_reference, best)
                + _render_requirements_matrix(data, ctx, has_reference)
                + _render_plots(path))
    else:
        body = _render_header(ctx, title, solutions, has_reference) + _render_setup(ctx) + \
            '<h2>Solutions</h2><p class="muted">No unpenalized candidate sets were found.</p>' + _render_plots(path)

    summary = {
        "objectives": " + ".join(ctx.objective_label(o) for o in ctx.objectives),
        "elements": ", ".join(ctx.stat_label(e) for e in ctx.elements),
        "candidates": len(candidates),
        "best": data[best] if best is not None else None,
        "best_weapon": ctx.name(data[best]["weapon"]) if best is not None and data[best]["weapon"] else "none",
        "reference": data[0] if has_reference and data else None,
    }
    return _page(title, body), summary


def write_html_report(optimizer, solutions, has_reference=False, title=None):
    """Write report.html into the run's output path and return its summary."""
    page, summary = build_report(optimizer, solutions, has_reference, title)
    filename = os.path.join(optimizer.config["path"], "report.html")
    with open(filename, "w", encoding="utf-8") as file:
        file.write(page)
    return summary


# --- Rebuilding reports for existing runs ---------------------------------

def _load_config(run_dir, character_class=None):
    with open(os.path.join(run_dir, "config.json")) as file:
        config = json.load(file)
    character = config["character"]
    if character_class:
        character["class"] = character_class
    for key in ("exo", "distributed_points"):
        character[key] = {int(k): v for k, v in character.get(key, {}).items()}
    preferences = config["optimizer"].get("preferences", {})
    config["optimizer"]["preferences"] = {b: {int(k): v for k, v in p.items()} for b, p in preferences.items()}
    config["optimizer"]["path"] = run_dir
    return config


def _load_solutions(run_dir):
    with open(os.path.join(run_dir, "report.txt")) as file:
        text = file.read()
    blocks = re.findall(r"Chromosome: \[\n(.*?)\]", text, flags=re.DOTALL)
    return [[int(i) for i in re.findall(r"^\s*(\d+),", block, flags=re.MULTILINE)] for block in blocks]


def rebuild_report(run_dir, character_class=None):
    """Re-evaluate the sets listed in a run's report.txt and write its report.html."""
    from character import Character
    from chromosome import Chromosome
    from data import item_sets, items
    from optimizer import Optimizer

    config = _load_config(run_dir, character_class)
    optimizer = Optimizer(Character(**config["character"]), items, item_sets, **config["optimizer"])
    solutions = []
    for ids in _load_solutions(run_dir):
        # Items filtered out by the optimizer (e.g. an old reference set) are still evaluated
        for i in ids:
            if i not in optimizer.items and i in items:
                optimizer.items[i] = items[i]
                if items[i].get("hasParentSet"):
                    set_id = items[i]["parentSet"]["id"]
                    optimizer.item_sets.setdefault(set_id, item_sets[set_id])
        solutions.append(Chromosome([i for i in ids if i in items], optimizer))
    has_reference = bool(config["optimizer"].get("reference"))
    return write_html_report(optimizer, solutions, has_reference)


def _find_runs(root):
    if os.path.exists(os.path.join(root, "config.json")):
        return [root]
    runs = []
    for directory, _, files in os.walk(root):
        if "config.json" in files and "report.txt" in files:
            runs.append(directory)
    return sorted(runs)


class _MaestroLoader(yaml.SafeLoader):
    """Safe YAML loader that also reads the OrderedDicts Maestro writes into meta/parameters.yaml."""


_MaestroLoader.add_constructor("tag:yaml.org,2002:python/object/apply:collections.OrderedDict",
                               lambda loader, node: loader.construct_sequence(node, deep=True))


def _sweep_parameters(root):
    """Map each run folder of a Maestro study to its swept parameters ({name: value}), or {} if unavailable."""
    path = os.path.join(root, "meta", "parameters.yaml")
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as file:
            combos = yaml.load(file, Loader=_MaestroLoader) or {}
    except yaml.YAMLError:
        return {}
    runs = {}
    for combo in combos.values():
        # Maestro names a run's folder after its sorted labels, with spaces replaced by underscores
        labels = [str(label).replace(" ", "_") for _, label in combo["labels"][0]]
        params = {name.strip("$()"): value for name, value in combo["params"].items()}
        runs[".".join(sorted(labels))] = (labels, params)
    return runs


def _run_parameters(run_dir, sweep):
    folder = os.path.basename(os.path.normpath(run_dir))
    if folder in sweep:
        return sweep[folder][1]
    # Fall back to the run whose labels all appear in the folder name
    for labels, params in sweep.values():
        if all(label in folder for label in labels):
            return params
    return None


def write_index(root, entries):
    """Write index.html in root, comparing the best set of every run below it."""
    sweep = _sweep_parameters(root)
    run_params = [_run_parameters(run_dir, sweep) for run_dir, _ in entries]
    # A Maestro sweep gets one column per parameter instead of the run folder name
    param_names = list(dict.fromkeys(k for p in run_params if p for k in p)) if all(run_params) else []
    show_objective = "OBJECTIVE" not in param_names
    show_elements = "ELEMENTS" not in param_names

    rows = []
    for (run_dir, summary), params in zip(entries, run_params):
        best = summary["best"]
        rel = os.path.relpath(run_dir, root)
        link = _esc(os.path.join(rel, "report.html"))
        if param_names:
            run_cells = "".join(
                f'<td class="{"num" if isinstance(params.get(k), (int, float)) else ""}">{_esc(params.get(k, "—"))}</td>'
                for k in param_names)
            run_cells += f'<td><a href="{link}" title="{_esc(rel)}">Open ↗</a></td>'
        else:
            run_cells = f'<td><a href="{link}">{_esc(rel)}</a></td>'
        if show_objective:
            run_cells += f'<td>{_esc(summary["objectives"])}</td>'
        if show_elements:
            run_cells += f'<td class="small">{_esc(summary["elements"])}</td>'

        if best:
            cls, text = best["status"]
            met = sum(r["met"] for r in best["requirements"])
            total = len(best["requirements"])
            met_cls = ("ok" if met == total else "bad") if total else ""
            status = f'<span class="badge bad">{_esc(text)}</span>' if cls == "bad" else ""
            best_cells = (f'<td class="num">{_fmt(best["fitness"])}</td>'
                          f'<td class="num met-{met_cls}">{met}/{total}</td><td>{status}</td>'
                          f'<td>{_esc(summary["best_weapon"])}</td>')
        else:
            best_cells = '<td class="num">—</td><td class="num muted">—</td><td><span class="badge bad">No candidates</span></td><td></td>'
        ref = summary["reference"]
        ref_cell = f'<td class="num">{_fmt(ref["fitness"])}</td>' if ref else '<td class="num muted">—</td>'
        rows.append(f"<tr>{run_cells}{best_cells}{ref_cell}<td class=\"num\">{summary['candidates']}</td></tr>")

    if param_names:
        heads = "".join(f"<th>{_esc(k)}</th>" for k in param_names) + "<th>Report</th>"
    else:
        heads = "<th>Run</th>"
    heads += ("<th>Objective</th>" if show_objective else "") + ("<th>Elements</th>" if show_elements else "")
    title = os.path.basename(os.path.normpath(root))
    body = f"""
<header><h1>{_esc(title)}</h1><div class="muted small">{len(entries)} run{"s" if len(entries) != 1 else ""} · generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</div></header>
<h2>Runs</h2>
<div class="scroll"><table>
<thead><tr>{heads}<th class="num">Best fitness</th><th class="num">Targets met</th><th>Problems</th>
<th>Best weapon</th><th class="num">Reference fitness</th><th class="num">Candidates</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>"""
    with open(os.path.join(root, "index.html"), "w", encoding="utf-8") as file:
        file.write(_page(title, body))


def main():
    parser = argparse.ArgumentParser(description="Build HTML reports for existing optimization runs")
    parser.add_argument("paths", nargs="+", help="Run directories, or directories containing runs (e.g. a Maestro study)")
    parser.add_argument("--class", dest="character_class", choices=DOFUS_FORGE_CLASSES, default=None,
                        help="Character class for Dofus Forge links, overriding the one saved with the run")
    args = parser.parse_args()
    for root in args.paths:
        runs = _find_runs(root)
        if not runs:
            print(f"No runs found in {root}")
            continue
        entries = []
        for run_dir in runs:
            print(f"Rendering {run_dir}")
            entries.append((run_dir, rebuild_report(run_dir, args.character_class)))
        if len(runs) > 1 or os.path.abspath(runs[0]) != os.path.abspath(root):
            write_index(root, entries)
            print(f"Wrote {os.path.join(root, 'index.html')}")


if __name__ == "__main__":
    main()
