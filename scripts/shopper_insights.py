"""Daily shopper insights from the flight log (saved chats) and the catalogue.

Finds what shoppers have in common, what they ask for that we don't carry, and
stock problems, then writes output/shopper_insights.md with recommendations.

Run from the My Work folder:
    python scripts/shopper_insights.py
"""

import re
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "campus_customs.db"
OUT = ROOT / "output" / "shopper_insights.md"

# What shoppers talk about -> words that signal it.
THEMES = {
    "Hoodies & fleece (warm layers)": r"hood|fleece|jacket|quarter|zip|crewneck|sweat",
    "Tees": r"\btee|t-?shirt",
    "Mascot / bulldog / Handsome Dan": r"bulldog|handsome dan|\bdan\b|mascot",
    "Colors": r"\bpink|blue|navy|gr[ae]y|white|black|red|green|color",
    "Sizes & stock": r"\bsize|\b(xs|s|m|l|xl|xxl)\b|medium|large|small|in stock|left",
    "Price & value": r"cheap|price|cost|how much|deal|sale|\$",
    "Gym / athletic": r"gym|athletic|workout|shorts|running|sport",
    "Account & memory": r"remember|my name|email|account|password",
}
# Things shoppers might want that the catalogue doesn't have (checked against the catalogue).
WANTS = {
    "gym shorts": r"shorts",
    "Handsome Dan designs": r"handsome dan",
    "pink items": r"\bpink",
    "kids / youth sizes": r"\bkid|youth|toddler|baby",
    "hats & caps": r"\bhat\b|\bcap\b|beanie",
    "mugs, bags, bottles": r"mug|tote|bag|bottle",
}


def main() -> None:
    conn = sqlite3.connect(f"{DB.as_uri()}?mode=ro", uri=True)
    asks = conn.execute(
        "SELECT callsign, transmission FROM flight_log WHERE speaker = 'PILOT' ORDER BY msg_id"
    ).fetchall()
    catalogue_text = " ".join(
        r[0].lower() for r in conn.execute("SELECT name || ' ' || description || ' ' || search_tags || ' ' || colors FROM catalogue")
    )
    pilots = {c for c, _ in asks}

    theme_hits: Counter = Counter()
    theme_pilots: dict[str, set] = {t: set() for t in THEMES}
    for callsign, text in asks:
        for theme, pattern in THEMES.items():
            if re.search(pattern, text.lower()):
                theme_hits[theme] += 1
                theme_pilots[theme].add(callsign)

    unmet = []
    for want, pattern in WANTS.items():
        asked_by = sorted({c for c, t in asks if re.search(pattern, t.lower())})
        # "shorts" must not match "short-sleeve" in the catalogue
        carried = re.search(r"(?<!short-sleeve )" + pattern if want != "gym shorts" else r"\bshorts\b", catalogue_text)
        if not carried:
            unmet.append((want, asked_by))

    sold_out = conn.execute("SELECT COUNT(*) FROM inventory WHERE quantity = 0").fetchone()[0]
    low = conn.execute("SELECT COUNT(*) FROM inventory WHERE quantity BETWEEN 1 AND 5").fetchone()[0]
    rows = conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
    budget = conn.execute("SELECT COUNT(*) FROM catalogue WHERE price < 40").fetchone()[0]
    nearly_gone = conn.execute(
        "SELECT c.name, SUM(i.quantity) t FROM inventory i JOIN catalogue c USING(product_id) GROUP BY 1 ORDER BY t LIMIT 3"
    ).fetchall()

    lines = [
        "# Shopper Insights: Campus Customs",
        "",
        f"Generated {datetime.now():%b %d, %Y %I:%M %p} from `flight_log` ({len(asks)} shopper messages from {len(pilots)} logged-in pilots) and the catalogue.",
        "Rerun any day with `python scripts/shopper_insights.py`.",
        "",
        "## What shoppers have in common",
        "",
        "| Theme | Messages | Pilots |",
        "|---|---|---|",
    ]
    for theme, n in theme_hits.most_common():
        lines.append(f"| {theme} | {n} | {', '.join(sorted(theme_pilots[theme]))} |")
    lines += ["", "## Asked for or likely wanted, but not in the catalogue", ""]
    for want, who in unmet:
        lines.append(f"- **{want}**: " + (f"asked by {', '.join(who)}" if who else "not asked yet, but a gap for new kinds of customers"))
    lines += [
        "",
        "## Stock watch",
        "",
        f"- **{sold_out} of {rows}** size slots are sold out, and **{low}** have only 1–5 left.",
        "- Lowest total stock: " + "; ".join(f"{n} ({t})" for n, t in nearly_gone) + ".",
        f"- **{budget}** items are under $40 (all tees), so budget shoppers have options.",
        "",
        "## Recommendations",
        "",
        "1. **Fill the gaps shoppers asked about**: gym shorts, Handsome Dan designs and pink colorways. Until then, Chloe should offer the closest real items (she does).",
        "2. **\"Notify me\" for sold-out sizes.** With this many empty size slots, let pilots leave an email and get a radio call when it's back.",
        "3. **\"Last call\" badges** on 1–5-left sizes create urgency and help shoppers grab their size.",
        "4. **Personal radar for returning pilots**: use their flight log to suggest items on their next visit (e.g. a fleece fan sees new fleece first).",
        "5. **Attract new kinds of customers**: kids/youth sizes for families, accessories (hats, mugs, totes) for gift-buyers and alumni, and a value \"Under $40\" lane for students.",
        "6. **Keep it fun**: a daily \"Find Dan\" game, Bulldog Miles for chats and visits, and shareable cargo-drop reels.",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
