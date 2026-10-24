"""Tools Chloe can call, plus the model connection (Portkey).

The model is reached through Portkey's OpenAI-compatible gateway, the same
pattern as Homework 3. Set PORTKEY_API_KEY (and optionally OPENAI_MODEL) in
the environment or in a .env file (see .env.example).

Product tools read data/campus_customs.db through a read-only connection, so
every price, description and stock number Chloe gives comes from the database.
"""

import difflib
import json
import math
import os
import re
import sqlite3
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic_ai import ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

import reels
from models import (
    CatalogueHit, CatalogueSearch, ChatDeps, CurrentPage, PageContext, PilotProfile, ViewedProduct, ProductCard, ProductInfo, ProductMatch,
    SizeStock, StockReport, StoreInfo,
)

HERE = Path(__file__).resolve().parent
# A .env next to the backend, or one level up in the project root, both work.
load_dotenv(HERE / ".env")
load_dotenv(HERE.parent / ".env")

DB_PATH = HERE.parent / "data" / "campus_customs.db"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

# Over-purchasing gates (also stated in prompts/prompt.md).
MAX_PER_ITEM = 10
MAX_PER_ORDER = 25

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
MAX_MATCHES = 12  # hard cap for find_products(limit=...)
FLAIR: dict[str, dict[str, str]] = json.loads((HERE / "product_flair.json").read_text(encoding="utf-8"))


class MissingApiKey(Exception):
    """PORTKEY_API_KEY isn't set, so the agent can't reach a model."""


def make_model() -> OpenAIResponsesModel:
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise MissingApiKey("PORTKEY_API_KEY is not set. Add it to .env (see .env.example).")
    provider = OpenAIProvider(base_url=PORTKEY_BASE_URL, api_key=api_key)
    return OpenAIResponsesModel(MODEL_NAME, provider=provider)


def _db() -> sqlite3.Connection:
    """Read-only connection: tools can look things up but can never change prices or stock."""
    conn = sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- matching helpers ----------

# Spellings shoppers use -> the words the catalogue uses.
_SYNONYMS = [
    # Handsome Dan is Yale's bulldog mascot: shoppers asking for him want bulldog designs.
    (r"\bhandsome\s+dan\b|\bmascot\b|\bbull\s?dogs?\b", "bulldog"),
    (r"\b1\s*/\s*4\b|\bquarter\b|\b1 4\b", "quarterzip"),
    (r"\bt[\s-]?shirts?\b|\btees?\b", "tshirt"),
    (r"\bhood(ie|ies|ed)?\b|\bhoods\b", "hoodie"),
    (r"\bcrew[\s-]?necks?\b|\bcrews\b", "crewneck"),
    (r"\bsweat[\s-]?shirts?\b", "sweatshirt"),
    (r"\bjackets?\b", "jacket"),
]
_STOPWORDS = {
    "the", "a", "an", "do", "does", "you", "have", "has", "any", "in", "for", "with", "and", "or",
    "of", "is", "are", "it", "this", "that", "how", "much", "many", "what", "whats", "price", "cost",
    "stock", "left", "size", "sizes", "my", "me", "i", "can", "get", "your", "got", "yale", "zip",
    "one", "item", "please", "there", "available",
}


def _normalize(text: str) -> str:
    text = text.lower().replace("-", " ")
    for pattern, word in _SYNONYMS:
        text = re.sub(pattern, word, text)
    return text


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", _normalize(text)) if t not in _STOPWORDS]


_SIZE_WORDS = {
    "xs": "XS", "extra small": "XS", "x small": "XS", "xsmall": "XS",
    "s": "S", "small": "S", "sm": "S",
    "m": "M", "medium": "M", "med": "M",
    "l": "L", "large": "L", "lg": "L",
    "xl": "XL", "extra large": "XL", "x large": "XL", "xlarge": "XL",
    "xxl": "XXL", "2xl": "XXL", "xx large": "XXL", "double xl": "XXL", "extra extra large": "XXL",
}


def normalize_size(size: str) -> str:
    key = re.sub(r"[\s_-]+", " ", size.strip().lower())
    if key.upper() in SIZE_ORDER:
        return key.upper()
    if key in _SIZE_WORDS:
        return _SIZE_WORDS[key]
    raise ModelRetry(f"'{size}' is not a size we carry. Sizes are: {', '.join(SIZE_ORDER)}.")


def _get_row(conn: sqlite3.Connection, product_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
    if row is None:
        raise ModelRetry(
            f"No product has id '{product_id}'. Call find_products first and use an exact product_id from it."
        )
    return row


# ---------- tools ----------

def get_store_info() -> StoreInfo:
    """Facts about Campus Customs: address, contact email, what the shop sells, and order limits."""
    return StoreInfo(
        name="Campus Customs",
        address="57 Broadway, New Haven, CT 06511",
        contact_email="orderdept@campuscustoms.com",
        sells=["tees", "crewnecks", "hoodies", "quarter-zips", "fleece and jackets"],
        officially_licensed=True,
        max_per_item=MAX_PER_ITEM,
        max_per_order=MAX_PER_ORDER,
    )


def _closest_word(word: str, vocab: set[str]) -> str:
    """Return the word itself if the catalogue knows it, else its closest catalogue spelling."""
    if word in vocab or len(word) < 4 or word.isdigit():
        return word
    match = difflib.get_close_matches(word, vocab, n=1, cutoff=0.75)
    if not match:
        return word
    # Don't "fix" a real word into a shorter/longer one ("shorts" -> "short" from short-sleeve):
    # that would make products we don't sell look like matches.
    if match[0].startswith(word) or word.startswith(match[0]):
        return word
    return match[0]


def find_products(query: str, limit: int = 5) -> list[ProductMatch]:
    """Find catalogue products matching what the shopper typed (a name, style, college, sport or color).

    Returns the best matches with their exact product_id, at most `limit` (1-12).
    Use limit 5 to pin down one named item; use limit 8 when the shopper browses a
    category ("what hoodies do you have?"). An empty list means nothing in the
    catalogue matches, so do not suggest that item exists.
    """
    limit = max(1, min(limit, MAX_MATCHES))
    words = _tokens(query)
    if not words:
        return []
    with _db() as conn:
        rows = conn.execute("SELECT product_id, name, garment_type, colors, search_tags FROM catalogue").fetchall()
    fields = []
    for r in rows:
        fields.append((
            r,
            set(_tokens(r["name"] + " " + r["product_id"])),
            set(_tokens(r["garment_type"])),
            set(_tokens(" ".join(json.loads(r["search_tags"])))),
            set(_tokens(" ".join(json.loads(r["colors"])))),
        ))
    # Typo-proof (usability B5): a word the catalogue doesn't know ("hoddie", "saybrok") is
    # swapped for the closest catalogue word, so a misspelling still finds the right items.
    vocab = set().union(*(f for fs in fields for f in fs[1:]))
    words = [_closest_word(w, vocab) for w in words]
    # Rare words (a college, a sport) say more than common ones (hoodie), so weight by rarity.
    n = len(fields)
    weight = {w: math.log((n + 1) / (1 + sum(any(w in f for f in fs[1:]) for fs in fields))) + 1 for w in words}
    scored: list[tuple[float, sqlite3.Row]] = []
    for r, name, gtype, tags, colors in fields:
        score, hits = 0.0, 0
        for w in words:
            # Count each word once, at its best field: name 3 > type 2 > tags 1.5 > colors 1.
            pts = max(3 * (w in name), 2 * (w in gtype), 1.5 * (w in tags), 1 * (w in colors))
            score += pts * weight[w]
            hits += pts > 0
        if hits:
            scored.append((score + 2 * (hits == len(words)), r))  # bonus when every word matched
    if not scored:
        return []
    scored.sort(key=lambda x: (-x[0], x[1]["name"]))
    best = scored[0][0]
    return [
        ProductMatch(product_id=r["product_id"], name=r["name"], garment_type=r["garment_type"])
        for s, r in scored[:limit]
        if s >= best * 0.6
    ]


def get_product_info(product_id: str) -> ProductInfo:
    """Description, colors and price for one product. Use an exact product_id from find_products."""
    with _db() as conn:
        r = _get_row(conn, product_id)
    return ProductInfo(
        product_id=r["product_id"],
        name=r["name"],
        garment_type=r["garment_type"],
        description=r["description"],
        colors=json.loads(r["colors"]),
        price=r["price"],
    )


def get_stock(product_id: str, size: str | None = None) -> StockReport:
    """How many units are in stock for one product, size by size.

    Pass `size` (e.g. "M", "medium", "XL") when the shopper asks about one size;
    leave it out to get all six sizes. quantity 0 means that size is sold out.
    """
    wanted = normalize_size(size) if size else None
    with _db() as conn:
        r = _get_row(conn, product_id)
        rows = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()
    all_sizes = sorted(
        (SizeStock(size=s["size"], quantity=s["quantity"], in_stock=s["quantity"] > 0) for s in rows),
        key=lambda s: SIZE_ORDER.index(s.size),
    )
    shown = [s for s in all_sizes if s.size == wanted] if wanted else all_sizes
    return StockReport(
        product_id=r["product_id"],
        name=r["name"],
        requested_size=wanted,
        sizes=shown,
        sizes_in_stock=[s.size for s in all_sizes if s.in_stock],
        sold_out_sizes=[s.size for s in all_sizes if not s.in_stock],
        total_units=sum(s.quantity for s in all_sizes),
    )


# ---------- one-shot filtered search (usability B3) ----------

# Shopper words for a kind of garment -> test on the catalogue's garment_type.
CATEGORIES = {
    "hoodie": lambda g: "hood" in g and "zip" not in g,
    "full-zip hoodie": lambda g: "full-zip hood" in g,
    "crewneck": lambda g: "crewneck" in g or g == "crewneck",
    "tee": lambda g: "t-shirt" in g,
    "quarter-zip": lambda g: "quarter-zip" in g,
    "fleece / jacket": lambda g: "fleece" in g or "jacket" in g,
    "long-sleeve": lambda g: "long-sleeve" in g,
    "mockneck": lambda g: "mockneck" in g,
}
_CATEGORY_ALIASES = {
    "hoodie": "hoodie", "hoodies": "hoodie", "hood": "hoodie", "sweatshirt": "hoodie",
    "full zip": "full-zip hoodie", "full-zip": "full-zip hoodie", "zip hoodie": "full-zip hoodie",
    "crewneck": "crewneck", "crewnecks": "crewneck", "crew": "crewneck", "crew neck": "crewneck",
    "tee": "tee", "tees": "tee", "t-shirt": "tee", "t shirt": "tee", "tshirt": "tee", "shirt": "tee",
    "quarter-zip": "quarter-zip", "quarter zip": "quarter-zip", "1/4 zip": "quarter-zip", "1/4-zip": "quarter-zip",
    "fleece": "fleece / jacket", "jacket": "fleece / jacket", "jackets": "fleece / jacket",
    "long sleeve": "long-sleeve", "long-sleeve": "long-sleeve", "performance": "long-sleeve",
    "mockneck": "mockneck", "mock neck": "mockneck",
}


def _category(word: str | None) -> str | None:
    if not word:
        return None
    key = word.strip().lower()
    if key in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[key]
    close = difflib.get_close_matches(key, list(_CATEGORY_ALIASES), n=1, cutoff=0.75)  # typo-proof too
    if close:
        return _CATEGORY_ALIASES[close[0]]
    raise ModelRetry(f"Unknown category '{word}'. Use one of: {', '.join(CATEGORIES)}.")


def search_catalogue(
    category: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    color: str | None = None,
    size_in_stock: str | None = None,
    keywords: str | None = None,
    sort: Literal["price_low", "price_high", "name"] = "name",
    limit: int = 8,
) -> CatalogueSearch:
    """Find products matching ALL the given filters in one call, with price, colors and sizes in stock.

    Use for questions with conditions, e.g. "hoodies under $70 in medium", "navy crewnecks",
    "cheapest fleece" (category="fleece", sort="price_low"), "tees in XL". Every filter is optional:
    category (hoodie, crewneck, tee, quarter-zip, fleece / jacket, full-zip hoodie, long-sleeve, mockneck),
    max_price / min_price in dollars, color (e.g. "navy", "gray"), size_in_stock (e.g. "M"),
    keywords (a college, sport or design, e.g. "Saybrook", "bulldog"). Prices and sizes returned here
    come straight from the database and may be quoted.
    """
    cat = _category(category)
    size = normalize_size(size_in_stock) if size_in_stock else None
    want_color = re.sub(r"\bgrey\b", "gray", color.strip().lower()) if color else None
    keep_ids = {m.product_id for m in find_products(keywords, limit=MAX_MATCHES)} if keywords else None
    limit = max(1, min(limit, MAX_MATCHES))

    hits: list[CatalogueHit] = []
    with _db() as conn:
        for r in conn.execute("SELECT * FROM catalogue").fetchall():
            g = r["garment_type"].lower()
            if cat and not CATEGORIES[cat](g):
                continue
            if max_price is not None and r["price"] > max_price:
                continue
            if min_price is not None and r["price"] < min_price:
                continue
            colors = json.loads(r["colors"])
            if want_color and not any(want_color in c.lower() for c in colors):
                continue
            if keep_ids is not None and r["product_id"] not in keep_ids:
                continue
            stock = conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (r["product_id"],)).fetchall()
            in_stock = sorted((x["size"] for x in stock if x["quantity"] > 0), key=SIZE_ORDER.index)
            if size and size not in in_stock:
                continue
            hits.append(CatalogueHit(
                product_id=r["product_id"], name=r["name"], garment_type=r["garment_type"],
                price=r["price"], colors=colors, sizes_in_stock=in_stock,
            ))
    if sort == "price_low":
        hits.sort(key=lambda h: (h.price, h.name))
    elif sort == "price_high":
        hits.sort(key=lambda h: (-h.price, h.name))
    else:
        hits.sort(key=lambda h: h.name)
    applied = {k: str(v) for k, v in {
        "category": cat, "max_price": max_price, "min_price": min_price, "color": want_color,
        "size_in_stock": size, "keywords": keywords, "sort": sort,
    }.items() if v is not None}
    return CatalogueSearch(filters_applied=applied, total_matching=len(hits), matches=hits[:limit])


# ---------- product cards for the website (not a model tool) ----------

def build_product_cards(product_ids: list[str]) -> list[ProductCard]:
    """Turn product ids into display cards, reading every field from the database.

    Unknown ids are skipped, so the page can only ever show real products.
    """
    if not product_ids:
        return []
    with _db() as conn:
        cards: list[ProductCard] = []
        for pid in dict.fromkeys(product_ids):  # keep order, drop repeats
            r = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (pid,)).fetchone()
            if r is None:
                continue
            stock = conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (pid,)).fetchall()
            in_stock = sorted((s["size"] for s in stock if s["quantity"] > 0), key=SIZE_ORDER.index)
            first_sentence = re.split(r"(?<=[.!?])\s", r["description"].strip(), maxsplit=1)[0]
            cards.append(ProductCard(
                product_id=pid,
                name=r["name"],
                fun_name=FLAIR.get(pid, {}).get("fun_name", r["name"]),
                price=r["price"],
                garment_type=r["garment_type"],
                short_info=first_sentence,
                image_url=f"/images/{r['image_file_path']}",
                reel_url=reels.reel_url(pid),
                detail_url=f"/products/{pid}",
                sizes_in_stock=in_stock,
            ))
    return cards


# ---------- who is flying + where they are (Problem 8) ----------

def load_pilot(user_id: int) -> PilotProfile | None:
    """The logged-in shopper's profile for the agent. The password hash is never read."""
    with _db() as conn:
        r = conn.execute(
            "SELECT id, first_name, last_name, name, email, rank, callsign, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if r is None:
        return None
    return PilotProfile(
        user_id=r["id"],
        first_name=r["first_name"] or r["name"].split(" ")[0],
        last_name=r["last_name"] or "",
        email=r["email"],
        rank=r["rank"] or "Captain",
        callsign=r["callsign"] or "Bulldog",
        member_since=r["created_at"][:10],
    )


def resolve_page(page: PageContext) -> CurrentPage:
    """Turn the page the website reports into a CurrentPage, checking the product id against the catalogue."""
    with _db() as conn:
        def real_name(pid: str | None) -> str | None:
            if not pid:
                return None
            r = conn.execute("SELECT name FROM catalogue WHERE product_id = ?", (pid,)).fetchone()
            return r["name"] if r else None  # unknown ids from the browser are ignored

        name = real_name(page.product_id)
        pid = page.product_id if name else None
        recent = []
        for rid in dict.fromkeys(page.recent_product_ids):
            rname = real_name(rid)
            if rname and rid != pid:
                recent.append(ViewedProduct(product_id=rid, name=rname))
    return CurrentPage(path=page.path, product_id=pid, product_name=name, recently_viewed=recent[:4])


def get_pilot_profile(ctx: RunContext[ChatDeps]) -> PilotProfile | str:
    """Who you are talking to: name, email, rank, callsign and member-since date.

    Returns a note instead if the shopper is a guest (not logged in).
    """
    if ctx.deps.pilot is None:
        return "Guest pilot: not logged in, so no name or email on file. Call them 'Bulldog'."
    return ctx.deps.pilot


def get_current_page(ctx: RunContext[ChatDeps]) -> CurrentPage:
    """The page the shopper has open right now, plus item pages they viewed earlier this visit.

    If product_id is set, "this" / "it" means that product; "the one I saw before" means recently_viewed.
    """
    return ctx.deps.page
