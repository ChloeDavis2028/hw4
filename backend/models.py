"""Structured types for the Campus Customs chatbot (Chloe).

The agent's output is a RadioCall, so every reply arrives already split into
the parts of an ATC radio call. The API wraps it in a ChatResponse for the website.
"""

import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ChatTurn(BaseModel):
    """One earlier line of this chat session, sent by the website for context."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class PageContext(BaseModel):
    """Which page the shopper has open, sent with every chat message (Problem 8)."""

    path: str = Field(default="/", max_length=200, description="Website route, e.g. /products/basic-hoodie-big-yale")
    product_id: str | None = Field(default=None, max_length=120, description="Set when the shopper is on an item page.")
    recent_product_ids: list[str] = Field(
        default_factory=list, max_length=5, description="Item pages visited this visit, newest first."
    )


class ChatRequest(BaseModel):
    """What the website sends to POST /api/chat."""

    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = Field(
        default_factory=list, max_length=20,
        description="Guests only: this browser's recent lines. Logged-in pilots' history is loaded from the database.",
    )
    page: PageContext = Field(default_factory=PageContext)


# ---------- who is flying (agent deps, Problem 8) ----------

class PilotProfile(BaseModel):
    """The logged-in shopper, as Chloe sees them. Never includes the password hash."""

    user_id: int
    first_name: str
    last_name: str
    email: str
    rank: str
    callsign: str = Field(description='Fun radio callsign, e.g. "Firebird". Use it as to_station.')
    member_since: str


class ViewedProduct(BaseModel):
    product_id: str
    name: str


class CurrentPage(BaseModel):
    """What the shopper is looking at right now; "this" / "it" refers to this product."""

    path: str
    product_id: str | None = None
    product_name: str | None = None
    recently_viewed: list[ViewedProduct] = Field(
        default_factory=list, description='Other item pages opened this visit, newest first ("the one I saw before").'
    )


@dataclass
class ChatDeps:
    """Agent deps for one chat turn: who is flying, and which page they have open.

    Passed to agent.run(deps=...), read by the pilot briefing in agent.py and by the
    get_pilot_profile / get_current_page tools. pilot is None for guests.
    """

    pilot: PilotProfile | None
    page: CurrentPage


class SavedTurn(BaseModel):
    """One saved line of a logged-in pilot's chat, as returned by GET /api/chat/history."""

    role: Literal["user", "assistant"]
    content: str
    products: list["ProductCard"] = Field(default_factory=list)
    created_at: str


class RadioCall(BaseModel):
    """Chloe's reply, shaped like an air traffic control radio call."""

    to_station: str = Field(description='Callsign of the shopper being called, e.g. "Bulldog".')
    from_station: Literal["Yale Tower"] = Field(
        default="Yale Tower", description="Always Yale Tower."
    )
    message: str = Field(description="The actual answer, 1-3 short sentences with a light radio flavor.")
    sign_off: Literal["Over.", "Out."] = Field(
        description='"Over." if the shopper is expected to reply, "Out." if the exchange is complete.'
    )
    show_product_ids: list[str] = Field(
        default_factory=list,
        max_length=8,
        description=(
            "Exact product_ids (from find_products this turn) to display on the website as product cards, "
            "best match first. Use when the shopper asks what products you have or about specific items. "
            "Leave empty for non-product questions."
        ),
    )

    @model_validator(mode="after")
    def _no_repeated_callsigns(self) -> "RadioCall":
        """The site already prints "<to_station>, Yale Tower," before the message, so trim any
        callsigns the model repeats at the start of the message (e.g. "Bulldog, Yale Tower, roger...")."""
        names = [re.escape(self.to_station), "yale tower", "campus customs tower", "tower", "chloe"]
        lead = re.compile(r"^\s*(?:(?:this is\s+)?(?:" + "|".join(names) + r")\b(?:\s+here)?\s*[,:;.—–-]*\s*)+", re.I)
        trimmed = lead.sub("", self.message)
        # The sign-off is added separately, so drop an "Over." / "Out." the model put at the end too.
        # Only when it stands alone as the last sentence ("...$68. Over."), not "all over." or "hand-out".
        trimmed = re.sub(r"(?:(?<=[.!?])|^)\s*(?:over|out)(?: and out)?\s*[.!]?\s*$", "", trimmed, flags=re.I).rstrip()
        if trimmed and trimmed[-1] not in ".!?":
            trimmed += "."
        if trimmed:
            self.message = trimmed
        return self

    def as_text(self) -> str:
        return f"{self.to_station}, {self.from_station}, {self.message} {self.sign_off}"


class StoreInfo(BaseModel):
    """Fixed facts about the shop, returned by the get_store_info tool."""

    name: str
    address: str
    contact_email: str
    sells: list[str]
    officially_licensed: bool
    max_per_item: int = Field(description="Most units of one product allowed in a single order.")
    max_per_order: int = Field(description="Most items allowed in a single order; larger orders go to orderdept.")


# ---------- product lookup results (Problem 6 tools) ----------

class ProductMatch(BaseModel):
    """One catalogue hit from find_products. Just enough to pick the right item."""

    product_id: str = Field(description="Exact id to pass to get_product_info / get_stock.")
    name: str
    garment_type: str


class ProductInfo(BaseModel):
    """Description and price for one product, straight from the catalogue table."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str] = Field(description="Listed colors; empty means the catalogue lists none.")
    price: float = Field(description="Price in US dollars from the database. Quote exactly.")


class SizeStock(BaseModel):
    size: str = Field(description="XS, S, M, L, XL or XXL")
    quantity: int = Field(description="Units on hand from the inventory table. 0 means sold out.")
    in_stock: bool


class StockReport(BaseModel):
    """Stock for one product, all sizes or one requested size, from the inventory table."""

    product_id: str
    name: str
    requested_size: str | None = Field(description="The size asked about, normalized (e.g. 'medium' -> 'M').")
    sizes: list[SizeStock] = Field(description="The requested size only, or all six sizes in order.")
    sizes_in_stock: list[str]
    sold_out_sizes: list[str]
    total_units: int = Field(description="Units across all sizes.")


class CatalogueHit(BaseModel):
    """One product from search_catalogue, with the facts needed to filter and compare."""

    product_id: str
    name: str
    garment_type: str
    price: float = Field(description="Price in US dollars from the database. Quote exactly.")
    colors: list[str]
    sizes_in_stock: list[str] = Field(description="Sizes with quantity > 0 right now.")


class CatalogueSearch(BaseModel):
    """Result of search_catalogue: every product matching ALL the filters (usability B3)."""

    filters_applied: dict[str, str]
    total_matching: int = Field(description="How many products match; matches may be capped by limit.")
    matches: list[CatalogueHit]


class ProductCard(BaseModel):
    """A product the website shows as a card when Chloe finds matches. Built from the database, not by the model."""

    product_id: str
    name: str = Field(description="Real catalogue name.")
    fun_name: str = Field(description="Playful display name from product_flair.json.")
    price: float
    garment_type: str
    short_info: str = Field(description="First sentence of the catalogue description.")
    image_url: str
    reel_url: str = Field(description="Looping promo GIF made from the product photo.")
    detail_url: str = Field(description="Website route of the single-item page.")
    sizes_in_stock: list[str]


class ChatResponse(BaseModel):
    """What POST /api/chat returns to the website."""

    reply: str = Field(description="The radio call as one line of text, ready to display.")
    radio: RadioCall
    products: list[ProductCard] = Field(default_factory=list)
    callsign: str = Field(default="Bulldog", description="Callsign Chloe used for this pilot.")
    tools_used: list[str] = Field(
        default_factory=list,
        description="Tools the agent called this turn, in order. Shows that prices and stock came from the database.",
    )


SavedTurn.model_rebuild()
