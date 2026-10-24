"""Generate a fun name and a cheery, flowery blurb for every catalogue product.

The blurbs sprinkle in a few aviator and combat terms for fun. Facts (color,
garment, motif) come from the database; only the playful wording is invented.
Price and stock are never written here; the site always reads them live.

Run from the My Work folder:
    python scripts/make_flair.py
Writes backend/product_flair.json keyed by product_id.
"""

import hashlib
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "campus_customs.db"
OUT_PATH = ROOT / "backend" / "product_flair.json"

# Map the 22 messy garment_type labels onto a few families.
def family(garment_type: str) -> str:
    g = garment_type.lower()
    if "quarter-zip" in g:
        return "quarter_zip"
    if "full-zip hood" in g:
        return "full_zip"
    if "fleece" in g or "jacket" in g:
        return "fleece"
    if "performance" in g:
        return "performance"
    if "mockneck" in g:
        return "mockneck"
    if "hood" in g:
        return "hoodie"
    if "crewneck" in g:
        return "crewneck"
    return "tee"

FAMILY_WORD = {
    "tee": "tee",
    "crewneck": "crewneck",
    "hoodie": "hoodie",
    "quarter_zip": "quarter-zip",
    "full_zip": "full-zip hoodie",
    "fleece": "jacket",
    "performance": "long-sleeve",
    "mockneck": "mockneck",
}

FUN_NOUNS = {
    "tee": ["Tailwind Tee", "Sunbeam Sortie Tee", "Breezy Wingman Tee", "Blue Skies Tee", "Daisy Dogfight Tee", "Runway Rosebud Tee"],
    "crewneck": ["Cozy Co-Pilot Crew", "Velvet Vanguard Crew", "Moonlit Maneuver Crew", "Petal Patrol Crew", "Cloud Nine Crew", "Honeysuckle Hangar Crew"],
    "hoodie": ["Cloud Cocoon Hoodie", "Hangar Hug Hoodie", "Sky Snuggler Hoodie", "Starlight Squadron Hoodie", "Marshmallow Missile Hoodie", "Dreamy Dogfighter Hoodie"],
    "quarter_zip": ["Zephyr Zip", "Crosswind Quarter-Zip", "Lavender Liftoff Zip", "Jetstream Zip", "Rose-Petal Recon Zip"],
    "full_zip": ["Full-Throttle Hood", "Afterglow Airlift Hood"],
    "fleece": ["Fleece Flying Ace", "Sky Marshal Jacket", "Bomber of Bliss", "Velvet Vector Jacket", "Garden Gunship Jacket"],
    "performance": ["Afterburner Long-Sleeve", "Sprint Squadron Long-Sleeve"],
    "mockneck": ["Mock-Turtle Maverick"],
}

OPENERS = [
    "Oh, sweet springtime of style!",
    "Behold, a petal-soft daydream!",
    "Gather 'round, darling Bulldogs!",
    "Hark, a bouquet of pure delight!",
    "Ah, joy blooming like a garden at dawn!",
    "Sing out, sunshine!",
    "What a dazzling little sunrise!",
    "Gentle breezes, rejoice!",
    "Swoon, sweet friends!",
    "Hearts aflutter, everyone!",
]

BODIES = [
    "This {color} {word} blossoms with {motif} pride and wraps you in cloud-spun comfort",
    "Kissed in {color}, this {word} carries {motif} spirit like a meadow carries wildflowers",
    "This dreamy {color} {word} hums with {motif} charm, soft as a lullaby and twice as sweet",
    "Spun in {color} and sprinkled with {motif} magic, this {word} feels like a hug from a sunbeam",
    "This {word} glows in {color}, a love letter to {motif} written in the coziest ink",
    "Petal by petal, this {color} {word} unfurls {motif} joy all over your day",
]

CLOSERS = [
    "Cleared for takeoff on every quad stroll.",
    "Mission accomplished: maximum cozy, zero casualties.",
    "Roger that, wingman, your style is locked on target.",
    "Engage afterburners and charge into finals week!",
    "Your trusty co-pilot for every campus sortie.",
    "Deploy on game day and capture the high ground.",
    "Altitude: fabulous. Status: battle-ready.",
    "Flaps down, smiles up, prepare for a perfect landing.",
    "Hold the line, Bulldog; comfort reinforcements have arrived.",
    "Fly in formation with your fellow Elis and own the skies.",
    "Radar confirms it: a direct hit of cuteness.",
    "Report for duty in total, petal-soft splendor.",
]

# Best way to wear each garment family: practical tips, a dash of flight-deck fun.
BEST_USE = {
    "tee": [
        "Wear it solo on warm days on Old Campus, or tuck it under an open flannel when the breeze picks up.",
        "Pair it with jeans for class and shorts for the Green; it is your everyday wingman from move-in to May.",
        "Layer it under a crewneck on crisp mornings, then peel down to just the tee by afternoon.",
    ],
    "crewneck": [
        "Throw it over a collared shirt for a polished study-session look, or wear it solo with joggers for late nights.",
        "Your go-to layer for chilly lecture halls: size up for a roomy, cozy fit.",
        "Pair it with jeans on game day, then keep it on for the dining-hall debrief.",
    ],
    "hoodie": [
        "Hood up for windy walks down Hillhouse; layer a tee underneath for those 8 a.m. sorties.",
        "Perfect for the stands on a cold game day. Stash your phone in the front pocket and settle in.",
        "Wear it as your cozy base layer under a winter coat, then fly solo once you reach the library.",
    ],
    "quarter_zip": [
        "Zip it up over a button-down for a sharp, interview-ready look, or wear it half-zipped on a cool afternoon.",
        "Layer it over a long-sleeve tee for fall: smart enough for a networking event, comfy enough for the library.",
        "Great for travel: throw it on at the gate and you are cleared for a comfy flight home.",
    ],
    "full_zip": [
        "Zip up for the walk across campus, unzip once you land indoors: the easiest layer you will own.",
        "Wear it open over a tee on mild days, or zipped tight with the hood up when the wind rolls in.",
    ],
    "fleece": [
        "Your outer layer for crisp fall days and the Bowl; layer a hoodie underneath when winter arrives.",
        "Wear it over a quarter-zip or crewneck for a warm, put-together look on chilly mornings.",
        "Throw it on for tailgates and evening walks; it blocks the breeze without the bulk of a winter coat.",
    ],
    "performance": [
        "Built for workouts, runs and intramurals; it also layers neatly under a hoodie on cold mornings.",
        "Wear it to the gym or a run around East Rock, then straight to class without missing a beat.",
    ],
    "mockneck": [
        "Pair it with trousers or a skirt for a cozy-chic look, or with leggings for a relaxed weekend.",
    ],
}

GENERIC = {
    "yale", "t", "shirt", "tee", "hoodie", "hood", "crewneck", "crew", "1", "4", "zip", "left",
    "chest", "logo", "college", "sweater", "fleece", "jacket", "full", "mens", "basic",
    "tri", "blend", "heavyweight", "long", "sleeve", "l", "s", "2", "0", "double", "knit",
    "vit", "district", "ua", "champion", "brooks", "brothers", "reverse", "weave", "raglan",
    "triumph", "mockneck", "the", "vintage", "of", "school", "big", "sports",
}

def motif(name: str) -> str:
    words = [w for w in re.split(r"\s+", name) if w.lower() not in GENERIC]
    if words:
        return " ".join(words[:3])
    # Name was all generic words (e.g. "Basic Hoodie Big Yale"): use a classic nickname.
    return "Bulldog Blue"

def pick(options: list[str], key: str, salt: str) -> str:
    h = int(hashlib.sha256(f"{salt}:{key}".encode()).hexdigest(), 16)
    return options[h % len(options)]

def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM catalogue ORDER BY product_id").fetchall()

    flair: dict[str, dict[str, str]] = {}
    used_names: set[str] = set()
    for r in rows:
        pid = r["product_id"]
        fam = family(r["garment_type"])
        colors = json.loads(r["colors"])
        m = motif(r["name"])

        nouns = FUN_NOUNS[fam]
        start = int(hashlib.sha256(pid.encode()).hexdigest(), 16) % len(nouns)
        fun_name = ""
        for i in range(len(nouns)):
            candidate = f"The {m} {nouns[(start + i) % len(nouns)]}"
            if candidate not in used_names:
                fun_name = candidate
                break
        if not fun_name:
            fun_name = f"The {m} {nouns[start]} No. {len(used_names) + 1}"
        used_names.add(fun_name)

        body = pick(BODIES, pid, "body").format(color=colors[0] if colors else "Yale blue", word=FAMILY_WORD[fam], motif=m)
        blurb = f"{pick(OPENERS, pid, 'open')} {body}. {pick(CLOSERS, pid, 'close')}"
        flair[pid] = {"fun_name": fun_name, "fun_blurb": blurb, "best_use": pick(BEST_USE[fam], pid, "use")}

    OUT_PATH.write_text(json.dumps(flair, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(flair)} products to {OUT_PATH}")

if __name__ == "__main__":
    main()
