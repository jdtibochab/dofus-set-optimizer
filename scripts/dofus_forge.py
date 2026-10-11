"""
Share links for Dofus Forge (https://wembie.github.io/dofus-forge/), a Dofus 3
build planner that also uses dofusdude data, so item Ankama IDs match ours.

A link carries the whole build in its query string (schema v1 of
src/features/share/codec.ts in Wembie/dofus-forge):

    ?b=v1:<url-safe base64 of {"v":1,"c":class,"l":level,"g":"m","a":[...],"s":mask,"e":[...]}>
"""
import base64
import json

BASE_URL = "https://wembie.github.io/dofus-forge/"

CLASSES = [
    "cra", "ecaflip", "eniripsa", "enutrof", "eliotrope", "feca", "foggernaut",
    "forgelance", "huppermage", "iop", "masqueraider", "osamodas", "ouginak", "pandawa",
    "rogue", "sacrier", "sadida", "sram", "xelor",
]

# Dofus Forge CHARACTERISTICS order, as our stat IDs: vitality, wisdom, strength, intelligence, chance, agility
_CHARACTERISTICS = [9, 10, 45, 13, 22, 36]

# Dofus Forge ALL_SLOTS order
_SLOTS = [
    "hat", "cape", "amulet", "ring1", "ring2",
    "belt", "boots", "weapon", "shield", "companion",
    "sidekick",
    "dofus1", "dofus2", "dofus3", "dofus4", "dofus5", "dofus6",
]

# Item superTypeId -> candidate slots, filled in order
_SUPER_TYPE_SLOTS = {
    10: ["hat"],
    11: ["cape"],
    1: ["amulet"],
    3: ["ring1", "ring2"],
    4: ["belt"],
    5: ["boots"],
    2: ["weapon"],
    7: ["shield"],
    12: ["companion"],  # Pets, petsmounts and mounts
    27: ["companion"],
    13: ["dofus1", "dofus2", "dofus3", "dofus4", "dofus5", "dofus6"],  # Dofus, trophies, prysmaradites
}

# Languages Dofus Forge serves; others fall back to English
_LANGUAGES = {"es", "fr", "pt"}


def _equipped(items):
    equipped = {}
    for item in items:
        for slot in _SUPER_TYPE_SLOTS.get(item["type"]["superTypeId"], []):
            if slot not in equipped:
                equipped[slot] = item["ankama_id"]
                break
    return [equipped.get(slot) for slot in _SLOTS]


def build_url(items, character, name=None, language="en"):
    """Return a Dofus Forge link that loads the given items on the character."""
    allocated = getattr(character, "allocated", {})
    # --scrolled adds +100 to the four elemental characteristics only
    scrolled = 0
    if character.scrolled:
        for bit, stat in enumerate(_CHARACTERISTICS):
            if stat in (45, 13, 22, 36):
                scrolled |= 1 << bit

    snapshot = {
        "v": 1,
        "c": character.config.get("class") or "",
        "n": name[:60] if name else None,
        "l": character.level,
        "g": "m",
        "a": [int(allocated.get(stat, 0)) for stat in _CHARACTERISTICS],
        "s": scrolled,
        "e": _equipped(items),
    }
    snapshot = {k: v for k, v in snapshot.items() if v is not None}

    encoded = base64.urlsafe_b64encode(
        json.dumps(snapshot, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).decode("ascii").rstrip("=")
    lang_path = f"{language}/" if language in _LANGUAGES else ""
    return f"{BASE_URL}{lang_path}?b=v1:{encoded}"


def chromosome_url(chromosome, name=None):
    """Dofus Forge link for a Chromosome, in the run's report language."""
    optimizer = chromosome.optimizer
    return build_url(chromosome.items, optimizer.character, name=name,
                     language=optimizer.config.get("language", "en"))
