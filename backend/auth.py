"""Accounts for Campus Customs: password hashing, sign-up, login and sessions.

Passwords are never stored. We store pbkdf2_sha256$<salt>$<hash>, the same
format as the seeded test user:
  * PBKDF2-HMAC-SHA256, 120,000 iterations
  * a fresh random salt per user (the salt text, UTF-8 encoded, is the PBKDF2 salt)
  * login re-hashes the typed password with the stored salt and compares in
    constant time; nothing is ever "un-hashed"
"""

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 120_000
MIN_PASSWORD_LENGTH = 8

# Password-change schedule: remind pilots once a password is 180 days old.
PASSWORD_MAX_AGE_DAYS = 180

# Brute-force guard: 5 wrong passwords for one email locks it for 15 minutes.
MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 15 * 60

SESSION_SECONDS = 7 * 24 * 60 * 60
SECRET_PATH = Path(__file__).resolve().parent / ".session_secret"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthError(Exception):
    """A problem we can show to the shopper (status code + friendly message)."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


# ---------- password hashing ----------

def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS)
    return f"{ALGORITHM}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, salt, expected = stored.split("$")
    except ValueError:
        return False
    if algorithm != ALGORITHM:
        return False
    candidate = hash_password(password, salt).split("$")[2]
    return hmac.compare_digest(candidate, expected)


# Used when an email is unknown, so a wrong email takes as long as a wrong password.
_DUMMY_HASH = hash_password(secrets.token_hex(16))


# ---------- schema ----------

DEFAULT_RANK = "Captain"

# Fun pilot callsigns. Each shopper gets one, picked from their email so it never changes.
CALLSIGNS = [
    "Maverick", "Skyhawk", "Jetstream", "Tailwind", "Afterburner", "Nighthawk", "Thunderbolt",
    "Firebird", "Blue Angel", "Crosswind", "Sonic", "Stardust", "Wingnut", "Ace", "Contrail",
    "Barnstormer", "Sky Dancer", "Rocket", "Tumbleweed", "Bulldog One",
]


def make_callsign(email: str) -> str:
    h = int(hashlib.sha256(email.strip().lower().encode()).hexdigest(), 16)
    return CALLSIGNS[h % len(CALLSIGNS)]


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Add the columns our features need to users if they are missing.

    password_changed_at: for the 180-day password schedule.
    rank: the pilot rank the site greets them with (new pilots start as Captain).
    callsign: the fun pilot callsign Chloe calls them on the radio.
    Also creates the read-only `flight_log` view over chat_messages.
    """
    cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
    if "password_changed_at" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN password_changed_at TEXT")
        # Existing users: treat their password as set when the account was created.
        conn.execute("UPDATE users SET password_changed_at = created_at WHERE password_changed_at IS NULL")
    if "rank" not in cols:
        conn.execute(f"ALTER TABLE users ADD COLUMN rank TEXT NOT NULL DEFAULT '{DEFAULT_RANK}'")
    if "callsign" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN callsign TEXT")
    for uid, email in conn.execute("SELECT id, email FROM users WHERE callsign IS NULL").fetchall():
        conn.execute("UPDATE users SET callsign = ? WHERE id = ?", (make_callsign(email), uid))
    # Easy-to-read view of every saved chat: who, when, what was said, products shown.
    conn.execute("""
        CREATE VIEW IF NOT EXISTS flight_log AS
        SELECT m.id                                   AS msg_id,
               m.created_at                           AS time_utc,
               u.callsign                             AS callsign,
               u.rank || ' ' || COALESCE(u.first_name, u.name) AS pilot,
               u.email                                AS email,
               CASE m.role WHEN 'user' THEN 'PILOT' ELSE 'YALE TOWER' END AS speaker,
               m.content                              AS transmission,
               COALESCE(json_array_length(m.products_json), 0) AS products_shown
        FROM chat_messages m JOIN users u ON u.id = m.user_id
        ORDER BY m.id
    """)
    conn.commit()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def password_age_days(changed_at: str | None) -> int:
    if not changed_at:
        return 0
    then = datetime.strptime(changed_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - then).days


def public_user(row: sqlite3.Row) -> dict:
    """What the website may see about a user. password_hash is never included."""
    age = password_age_days(row["password_changed_at"])
    return {
        "id": row["id"],
        "first_name": row["first_name"] or row["name"].split(" ")[0],
        "last_name": row["last_name"] or "",
        "name": row["name"],
        "rank": row["rank"] or DEFAULT_RANK,
        "callsign": row["callsign"] or make_callsign(row["email"]),
        "email": row["email"],
        "created_at": row["created_at"],
        "password_changed_at": row["password_changed_at"],
        "password_age_days": age,
        "password_max_age_days": PASSWORD_MAX_AGE_DAYS,
        "password_change_due": age >= PASSWORD_MAX_AGE_DAYS,
    }


# ---------- validation ----------

def _clean_email(email: str) -> str:
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        raise AuthError(400, "Please enter a valid email address.")
    return email


def _check_new_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(400, f"Passwords need at least {MIN_PASSWORD_LENGTH} characters.")
    if password.lower() in {"password", "password1", "12345678", "qwertyui"}:
        raise AuthError(400, "That password is too easy to guess. Pick something stronger.")


# ---------- sign-up, login, change password ----------

def register(conn: sqlite3.Connection, first_name: str, last_name: str, email: str, password: str) -> sqlite3.Row:
    first_name, last_name = first_name.strip(), last_name.strip()
    if not first_name or not last_name:
        raise AuthError(400, "Please enter your first and last name.")
    email = _clean_email(email)
    _check_new_password(password)
    if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
        raise AuthError(409, "That email already has an account. Try logging in instead.")
    now = _now()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash, created_at, first_name, last_name, password_changed_at, callsign)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (f"{first_name} {last_name}", email, hash_password(password), now, first_name, last_name, now, make_callsign(email)),
    )
    conn.commit()
    return conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()


_failed: dict[str, list[float]] = {}


def login(conn: sqlite3.Connection, email: str, password: str) -> sqlite3.Row:
    email = email.strip().lower()
    recent = [t for t in _failed.get(email, []) if time.time() - t < LOCKOUT_SECONDS]
    _failed[email] = recent
    if len(recent) >= MAX_FAILED_LOGINS:
        raise AuthError(429, "Too many tries. This account is grounded for 15 minutes.")

    row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
    ok = verify_password(password, row["password_hash"] if row else _DUMMY_HASH)
    if not row or not ok:
        _failed[email].append(time.time())
        # Same message either way, so attackers can't learn which emails exist.
        raise AuthError(401, "That email and password combo didn't match. Check your instruments and try again.")
    _failed.pop(email, None)
    return row


def change_password(conn: sqlite3.Connection, user_id: int, current: str, new: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None or not verify_password(current, row["password_hash"]):
        raise AuthError(401, "Your current password isn't right.")
    _check_new_password(new)
    if verify_password(new, row["password_hash"]):
        raise AuthError(400, "Your new password must be different from the old one.")
    conn.execute(
        "UPDATE users SET password_hash = ?, password_changed_at = ? WHERE id = ?",
        (hash_password(new), _now(), user_id),
    )
    conn.commit()
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


# ---------- signed session tokens ----------

def _secret() -> bytes:
    env = os.environ.get("SESSION_SECRET")
    if env:
        return env.encode()
    if not SECRET_PATH.exists():
        SECRET_PATH.write_text(secrets.token_hex(32), encoding="utf-8")
    return SECRET_PATH.read_text(encoding="utf-8").strip().encode()


def make_token(user_id: int) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps({"uid": user_id, "exp": int(time.time()) + SESSION_SECONDS}).encode()
    ).decode()
    sig = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def read_token(token: str) -> int | None:
    try:
        payload, sig = token.split(".")
    except ValueError:
        return None
    good = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, good):
        return None
    data = json.loads(base64.urlsafe_b64decode(payload.encode()))
    if data["exp"] < time.time():
        return None
    return int(data["uid"])
