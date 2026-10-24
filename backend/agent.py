"""Chloe, the Campus Customs chatbot: a PydanticAI agent.

Wiring:
  * instructions = prompts/prompt.md (read once at startup)
  * model        = tools.make_model() (Portkey, OPENAI_MODEL)
  * tools        = get_store_info, find_products, get_product_info, get_stock,
                   get_pilot_profile, get_current_page
  * deps         = models.ChatDeps (who is flying + which page is open), also turned
                   into a short "pilot briefing" added to the instructions every turn
  * output       = models.RadioCall (a structured ATC radio call + product ids to show)
  * page cards   = tools.build_product_cards() turns those ids into ProductCards from the DB
  * audit trail  = _audit_record() appends every loop (steps + stop reason) to output/audit_trail.json
"""

import json
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from pydantic_ai import Agent, RunContext, capture_run_messages
from pydantic_ai.exceptions import ContentFilterError, ModelHTTPError, UsageLimitExceeded
from pydantic_ai.usage import UsageLimits

import tools
from models import ChatDeps, ChatResponse, ChatTurn, RadioCall

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "prompt.md"

# Keep each chat cheap and bounded. A typical stock question is: find_products ->
# get_product_info / get_stock -> answer, so allow a little headroom.
USAGE_LIMITS = UsageLimits(request_limit=6, tool_calls_limit=8)
HISTORY_TURNS = 12  # how many recent lines of the conversation the agent sees

_agent: Agent[ChatDeps, RadioCall] | None = None


def pilot_briefing(ctx: RunContext[ChatDeps]) -> str:
    """Dynamic instructions, rebuilt every turn from the deps: who is flying and where they are."""
    p, page = ctx.deps.pilot, ctx.deps.page
    if p:
        who = (
            f"You are talking with {p.rank} {p.first_name} {p.last_name} ({p.email}), "
            f'radio callsign "{p.callsign}", flying with us since {p.member_since}. '
            f'Use "{p.callsign}" as to_station and greet them by first name when it fits.'
        )
    else:
        who = 'You are talking with a guest pilot (not logged in). Use "Bulldog" as to_station; you do not know their name or email.'
    if page.product_id:
        where = (
            f'They are on the item page for "{page.product_name}" (product_id {page.product_id}). '
            'If they say "this", "it" or "this one", they mean that product: use that product_id directly.'
        )
    else:
        where = f"They are on the {page.path} page, not a single item."
    lines = [who, where]
    if page.recently_viewed:
        seen = "; ".join(f'"{v.name}" ({v.product_id})' for v in page.recently_viewed)
        lines.append(
            f"Earlier this visit they looked at: {seen}. "
            '"The other one", "the one I saw before" or "the first one" refer to these.'
        )
    return "PILOT BRIEFING\n" + "\n".join(f"- {x}" for x in lines)


def get_agent() -> Agent[ChatDeps, RadioCall]:
    """Build the agent on first use, so the API still starts if the key is missing."""
    global _agent
    if _agent is None:
        _agent = Agent(
            tools.make_model(),
            output_type=RadioCall,
            deps_type=ChatDeps,
            instructions=[PROMPT_PATH.read_text(encoding="utf-8"), pilot_briefing],
            tools=[
                tools.get_store_info, tools.find_products, tools.search_catalogue,
                tools.get_product_info, tools.get_stock,
                tools.get_pilot_profile, tools.get_current_page,
            ],
            retries=2,
        )
    return _agent


def _build_prompt(message: str, history: list[ChatTurn]) -> str:
    recent = history[-HISTORY_TURNS:]
    if not recent:
        return message
    log = "\n".join(f"{'PILOT' if t.role == 'user' else 'TOWER'}: {t.content}" for t in recent)
    return f"Flight log (earlier radio traffic with this pilot):\n{log}\n\nNew transmission from the pilot:\n{message}"


# Sent when the model provider's own safety filter blocks a message (e.g. a jailbreak attempt).
BLOCKED_CALL = RadioCall(
    to_station="Bulldog",
    message="unable, that request is outside what Tower can handle. Say again with a question about our Yale gear.",
    sign_off="Over.",
)


def _is_content_filter(err: Exception) -> bool:
    if isinstance(err, ContentFilterError):
        return True
    return isinstance(err, ModelHTTPError) and "content_filter" in str(err.body)


# ---------- "must call the tools" check for prices and stock ----------
# A reply that states a price must have called get_product_info this turn; a reply that
# states stock must have called get_stock. Otherwise the number could be invented.
PRICE_RE = re.compile(r"\$\s?\d")
STOCK_RE = re.compile(
    r"\b\d+\s+(?:left|in stock|units?|available|remaining|on hand)\b|\bsold out\b|\bout of stock\b|\bin stock\b",
    re.I,
)
NUDGE = (
    "Tower check: your last answer stated a {what} without calling {tool} in this turn. "
    "Prices and stock must come from the tools. Call find_products if needed, then {tool}, "
    "and answer again using only the tool results."
)
UNCONFIRMED_CALL = RadioCall(
    to_station="Bulldog",
    message="unable to confirm that from the stock room right now. The item's page under Products shows the live price and sizes left.",
    sign_off="Over.",
)


def _tools_called(messages: list) -> list[str]:
    return [
        p.tool_name
        for m in messages
        for p in getattr(m, "parts", [])
        if getattr(p, "part_kind", "") == "tool-call" and p.tool_name != "final_result"
    ]


def _found_ids(messages: list) -> set[str]:
    """product_ids a search tool actually returned this turn (the only ids allowed on the page)."""
    ids: set[str] = set()
    for m in messages:
        for p in getattr(m, "parts", []):
            if getattr(p, "part_kind", "") != "tool-return" or p.tool_name not in ("find_products", "search_catalogue"):
                continue
            items = p.content.matches if hasattr(p.content, "matches") else (
                p.content.get("matches", []) if isinstance(p.content, dict) else (p.content or [])
            )
            for item in items:
                pid = item.product_id if hasattr(item, "product_id") else (item or {}).get("product_id")
                if pid:
                    ids.add(pid)
    return ids


def _missing_tool(radio: RadioCall, called: list[str]) -> tuple[str, str] | None:
    """Return (what, tool) if the reply states a price or stock number its tools don't back up."""
    # search_catalogue returns database prices and sizes in stock, so it backs both kinds of claim.
    if PRICE_RE.search(radio.message) and not {"get_product_info", "search_catalogue"} & set(called):
        return "price", "get_product_info"
    if STOCK_RE.search(radio.message) and not {"get_stock", "search_catalogue"} & set(called):
        return "stock level", "get_stock"
    return None


# ---------- flight recorder: append-only audit trail (Problem 12) ----------
# Each chat turn adds ONE entry to output/audit_trail.json: time, flight number, callsign
# (never email), the question, every tool step (name, short args, short result), model
# requests, stop reason, reply and seconds. Append-only and never wiped: a restart keeps
# the file, and a damaged file is renamed, not deleted. No passwords, tokens or keys go in.
AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
AUDIT_SHORT = 160  # characters kept for args, results, questions and replies

_audit_lock = threading.Lock()


def _audit_short(value, limit: int = AUDIT_SHORT) -> str:
    """One readable line, cut to `limit` characters."""
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    text = value if isinstance(value, str) else json.dumps(value, default=str, ensure_ascii=False)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _audit_result(content) -> str:
    """Search tools return long lists; keep the count and the first few product ids."""
    if hasattr(content, "model_dump"):
        content = content.model_dump()
    matches = content.get("matches") if isinstance(content, dict) else content
    if isinstance(matches, list):
        ids = [getattr(m, "product_id", None) or (m.get("product_id") if isinstance(m, dict) else None) for m in matches]
        ids = [i for i in ids if i]
        more = f" +{len(ids) - 3} more" if len(ids) > 3 else ""
        return f"{len(ids)} matches: {', '.join(ids[:3])}{more}"
    if isinstance(content, dict):
        # Keep the facts (price, stock), drop long text like descriptions and file paths.
        facts = {k: v for k, v in content.items() if not (isinstance(v, str) and len(v) > 60)}
        if isinstance(facts.get("sizes"), list):  # stock: "L=0, M=25, …" instead of a list of objects
            facts["sizes"] = ", ".join(f"{s.get('size')}={s.get('quantity')}" for s in facts["sizes"] if isinstance(s, dict))
        return _audit_short(facts)
    return _audit_short(content)


def _audit_steps(messages: list) -> list[dict]:
    """Turn PydanticAI messages into flight-recorder steps (tool calls and their results)."""
    steps: list[dict] = []
    by_call_id: dict[str, dict] = {}
    for m in messages:
        for p in getattr(m, "parts", []):
            kind = getattr(p, "part_kind", "")
            if kind == "tool-call" and p.tool_name != "final_result":
                step = {"tool": p.tool_name, "args": _audit_short(p.args or {}), "result": None}
                steps.append(step)
                by_call_id[p.tool_call_id] = step
            elif kind == "tool-return" and p.tool_call_id in by_call_id:
                by_call_id[p.tool_call_id]["result"] = _audit_result(p.content)
            elif kind == "retry-prompt" and p.tool_call_id in by_call_id:
                by_call_id[p.tool_call_id]["result"] = "retry: " + _audit_short(p.content)
    return steps


def _audit_read() -> list:
    if not AUDIT_PATH.exists():
        return []
    try:
        data = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    # Damaged or not a list: keep it under another name (never wipe), then start fresh.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    AUDIT_PATH.rename(AUDIT_PATH.with_name(f"audit_trail.damaged-{stamp}.json"))
    return []


def _audit_record(entry: dict) -> None:
    """Append one entry. Writes to a temp file first, so a crash can't leave half a file."""
    with _audit_lock:
        try:
            AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
            entries = _audit_read()
            entry = {
                "time": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "flight": f"CC-{len(entries) + 1:04d}",
                **entry,
            }
            entries.append(entry)
            tmp = AUDIT_PATH.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            os.replace(tmp, AUDIT_PATH)
        except OSError as err:
            # The recorder must never take the radio down: report it and keep flying.
            print(f"[audit] could not write {AUDIT_PATH.name}: {err}")


async def run_chat(message: str, history: list[ChatTurn], deps: ChatDeps) -> ChatResponse:
    agent = get_agent()
    callsign = deps.pilot.callsign if deps.pilot else "Bulldog"
    called: list[str] = []
    found: set[str] = set()
    # Flight recorder (Problem 12): every step of every pass goes into output/audit_trail.json,
    # even when the loop ends in an error. capture_run_messages keeps the steps of a failed run.
    steps: list[dict] = []
    stop_reason = "error"
    requests = 0
    radio: RadioCall | None = None
    started = time.perf_counter()
    try:
        with capture_run_messages() as first_pass:
            try:
                result = await agent.run(_build_prompt(message, history), deps=deps, usage_limits=USAGE_LIMITS)
            finally:
                steps += _audit_steps(first_pass)
        requests += result.usage.requests
        radio = result.output
        called = _tools_called(result.new_messages())
        found = _found_ids(result.new_messages())
        stop_reason = "final answer"
        gap = _missing_tool(radio, called)
        if gap:  # one retry, with the conversation so far, telling Chloe to use her instruments
            what, tool = gap
            steps.append({"tool": "tower honesty check", "args": f"{what} stated without {tool}", "result": "retry"})
            earlier = len(result.all_messages())  # the retry pass replays these; log only its new steps
            with capture_run_messages() as retry_pass:
                try:
                    result = await agent.run(
                        NUDGE.format(what=what, tool=tool),
                        message_history=result.all_messages(),
                        deps=deps,
                        usage_limits=USAGE_LIMITS,
                    )
                finally:
                    steps += _audit_steps(retry_pass[earlier:])
            requests += result.usage.requests
            radio = result.output
            called += _tools_called(result.new_messages())
            found |= _found_ids(result.new_messages())
            stop_reason = "final answer after honesty retry"
            if _missing_tool(radio, called):
                radio = UNCONFIRMED_CALL  # never pass an unbacked price or stock number to a shopper
                stop_reason = f"unconfirmed: {what} not backed by {tool}"
    except (ContentFilterError, ModelHTTPError) as err:
        if not _is_content_filter(err):
            stop_reason = f"error: {type(err).__name__}"
            raise
        radio = BLOCKED_CALL
        stop_reason = "blocked by content filter"
    except UsageLimitExceeded as err:
        stop_reason = f"loop limit reached: {err}"
        raise
    except Exception as err:
        stop_reason = f"error: {type(err).__name__}"
        raise
    finally:
        if radio is not None and stop_reason.startswith("final answer") and radio.message.lstrip().lower().startswith("unable"):
            stop_reason += " (refused: safety rules)"
        _audit_record({
            "pilot": callsign,
            "logged_in": deps.pilot is not None,
            "page": deps.page.path,
            "question": _audit_short(message),
            "steps": steps,
            "model_requests": requests,
            "stop_reason": stop_reason,
            "reply": _audit_short(radio.as_text()) if radio else None,
            "seconds": round(time.perf_counter() - started, 1),
        })
    # Always address the pilot by their own callsign (guests are "Bulldog").
    radio = radio.model_copy(update={"to_station": callsign})
    # Cards for the page: only ids the search really returned, or the product on screen, built from the database.
    allowed = found | {v.product_id for v in deps.page.recently_viewed}
    if deps.page.product_id:
        allowed.add(deps.page.product_id)
    show = [pid for pid in radio.show_product_ids if pid in allowed]
    cards = tools.build_product_cards(show)
    return ChatResponse(reply=radio.as_text(), radio=radio, products=cards, callsign=callsign, tools_used=called)
