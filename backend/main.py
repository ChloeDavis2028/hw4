"""Campus Customs API.

Run from the backend/ folder:
    uvicorn main:app --reload --port 8000

A small API over data/campus_customs.db.

Products and images (Problem 3, read-only):
    GET  /api/products               all products with sizes and stock
    GET  /api/products/{product_id}  one product
    GET  /images/products/<file>     product photos from data/products/
    GET  /api/products/{id}/reel.gif funny promo reel made from the product photo (Problem 7, see reels.py)

Accounts (Problem 4, see auth.py):
    POST /api/auth/register          new pilot: saves a row in users (hashed password)
    POST /api/auth/login             returning pilot: email + password
    GET  /api/auth/me                who is logged in (Bearer token)
    POST /api/auth/change-password   180-day password schedule

Chat (Problem 5, see agent.py):
    POST /api/chat                   message in, Chloe's ATC radio call out
    GET  /api/chat/history           a logged-in pilot's saved chat, to reload when they return (Problem 8)
"""

import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import agent
import auth
import reels
from models import ChatDeps, ChatRequest, ChatResponse, ChatTurn, SavedTurn

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
DB_PATH = DATA_DIR / "campus_customs.db"
FLAIR_PATH = BASE_DIR / "product_flair.json"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# image_file_path in the catalogue is relative to data/, e.g. products/x.jpg
app.mount("/images", StaticFiles(directory=DATA_DIR), name="images")

# Fun names and cheery blurbs, keyed by product_id (made by scripts/make_flair.py)
FLAIR: dict[str, dict[str, str]] = json.loads(FLAIR_PATH.read_text(encoding="utf-8"))


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


with get_db() as _conn:
    auth.ensure_schema(_conn)


def product_dict(row: sqlite3.Row, sizes: list[sqlite3.Row]) -> dict:
    inventory = sorted(
        ({"size": s["size"], "quantity": s["quantity"]} for s in sizes),
        key=lambda s: SIZE_ORDER.index(s["size"]),
    )
    flair = FLAIR.get(row["product_id"], {})
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "fun_name": flair.get("fun_name", row["name"]),
        "fun_blurb": flair.get("fun_blurb", row["description"]),
        "best_use": flair.get("best_use", ""),
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        "image_file_path": row["image_file_path"],
        "image_url": f"/images/{row['image_file_path']}",
        "reel_url": reels.reel_url(row["product_id"]),
        "price": row["price"],
        "inventory": inventory,
        "total_stock": sum(s["quantity"] for s in inventory),
    }


@app.get("/api/products")
def list_products() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        stock = conn.execute("SELECT product_id, size, quantity FROM inventory").fetchall()
    by_product: dict[str, list[sqlite3.Row]] = {}
    for s in stock:
        by_product.setdefault(s["product_id"], []).append(s)
    return [product_dict(r, by_product.get(r["product_id"], [])) for r in rows]


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        sizes = conn.execute(
            "SELECT product_id, size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()
    return product_dict(row, sizes)


@app.get("/api/products/{product_id}/reel.gif")
def get_reel(product_id: str) -> FileResponse:
    """A short looping promo GIF for the product, generated from its photo on first request."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT product_id, name, image_file_path, price FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    path = reels.make_reel(row["product_id"], row["image_file_path"], row["price"], row["name"])
    return FileResponse(path, media_type="image/gif", headers={"Cache-Control": "public, max-age=86400"})


# ---------- accounts (Problem 4) ----------

class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


def _auth_response(user: sqlite3.Row) -> dict:
    return {"token": auth.make_token(user["id"]), "user": auth.public_user(user)}


def _current_user_id(authorization: str | None) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please log in first.")
    user_id = auth.read_token(authorization.removeprefix("Bearer "))
    if user_id is None:
        raise HTTPException(status_code=401, detail="Your session expired. Please log in again.")
    return user_id


@app.post("/api/auth/register", status_code=201)
def register(body: RegisterRequest) -> dict:
    try:
        with get_db() as conn:
            user = auth.register(conn, body.first_name, body.last_name, body.email, body.password)
    except auth.AuthError as e:
        raise HTTPException(status_code=e.status, detail=e.message)
    return _auth_response(user)


@app.post("/api/auth/login")
def login(body: LoginRequest) -> dict:
    try:
        with get_db() as conn:
            user = auth.login(conn, body.email, body.password)
    except auth.AuthError as e:
        raise HTTPException(status_code=e.status, detail=e.message)
    return _auth_response(user)


@app.get("/api/auth/me")
def me(authorization: str | None = Header(default=None)) -> dict:
    user_id = _current_user_id(authorization)
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="Account not found.")
    return {"user": auth.public_user(row)}


@app.post("/api/auth/change-password")
def change_password(body: ChangePasswordRequest, authorization: str | None = Header(default=None)) -> dict:
    user_id = _current_user_id(authorization)
    try:
        with get_db() as conn:
            user = auth.change_password(conn, user_id, body.current_password, body.new_password)
    except auth.AuthError as e:
        raise HTTPException(status_code=e.status, detail=e.message)
    return _auth_response(user)


# ---------- chat (Problems 5, 7 and 8) ----------

HISTORY_LIMIT = 40  # saved lines returned to the website when a pilot comes back


def _optional_user_id(authorization: str | None) -> int | None:
    """Logged-in pilot's id from the Bearer token, or None for a guest (or an expired token)."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return auth.read_token(authorization.removeprefix("Bearer "))


def _saved_turns(conn: sqlite3.Connection, user_id: int, limit: int) -> list[sqlite3.Row]:
    rows = conn.execute(
        "SELECT role, content, products_json, created_at FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    return list(reversed(rows))


def _save_turn(conn: sqlite3.Connection, user_id: int, role: str, content: str, products: list | None = None) -> None:
    conn.execute(
        "INSERT INTO chat_messages (user_id, role, content, products_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, role, content, json.dumps(products) if products else None, auth._now()),
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, authorization: str | None = Header(default=None)) -> ChatResponse:
    # Who is flying (agent deps) and which page they have open.
    user_id = _optional_user_id(authorization)
    pilot = agent.tools.load_pilot(user_id) if user_id else None
    deps = ChatDeps(pilot=pilot, page=agent.tools.resolve_page(body.page))

    # Logged-in pilots: the database is the memory. Guests: the browser sends its recent lines.
    if pilot:
        with get_db() as conn:
            rows = _saved_turns(conn, pilot.user_id, agent.HISTORY_TURNS)
        history = [ChatTurn(role=r["role"], content=r["content"]) for r in rows]
    else:
        history = body.history

    try:
        response = await agent.run_chat(body.message, history, deps)
    except agent.tools.MissingApiKey:
        raise HTTPException(status_code=503, detail="Chloe's radio is switched off: the AI key isn't configured.")
    except Exception:
        # Never pass raw provider errors to the browser; they can leak model or config details.
        raise HTTPException(status_code=502, detail="Chloe lost the radio signal. Please try again.")

    # Save both sides of the exchange to the pilot's flight log (chat_messages).
    if pilot:
        with get_db() as conn:
            _save_turn(conn, pilot.user_id, "user", body.message)
            _save_turn(conn, pilot.user_id, "assistant", response.reply, [c.model_dump() for c in response.products])
            conn.commit()
    return response


@app.get("/api/chat/history")
def chat_history(authorization: str | None = Header(default=None)) -> dict:
    """A returning pilot's saved chat (oldest first), so the widget can reload it."""
    user_id = _current_user_id(authorization)
    pilot = agent.tools.load_pilot(user_id)
    if pilot is None:
        raise HTTPException(status_code=401, detail="Account not found.")
    with get_db() as conn:
        rows = _saved_turns(conn, user_id, HISTORY_LIMIT)
    turns = []
    for r in rows:
        try:
            raw = json.loads(r["products_json"]) if r["products_json"] else []
        except json.JSONDecodeError:
            raw = []
        # Rebuild cards from the database so old saved snapshots never show stale prices.
        ids = [p.get("product_id") for p in raw if isinstance(p, dict) and p.get("product_id")]
        cards = agent.tools.build_product_cards(ids)
        turns.append(SavedTurn(role=r["role"], content=r["content"], products=cards, created_at=r["created_at"]))
    return {"callsign": pilot.callsign, "first_name": pilot.first_name, "rank": pilot.rank, "turns": turns}
