# Usability Improvements: Campus Customs (Problem 9)

Four improvements: **two for the website (front end)** and **two for Chloe and the backend**. Each one fixes a problem real shoppers hit. All four are live in the running app; the "See it" lines say exactly where.

| # | Improvement | Type | Fixes |
|---|---|---|---|
| F1 | Flight search and filters | Front end | Shoppers had to scroll all 102 products to find anything |
| F5 | Phone-friendly flight menu | Front end | On a phone the header covered about 300px, roughly a third of the screen |
| B3 | One-shot filter search for Chloe | Agent / backend | "Hoodies under $70 in medium" took several AI steps, and some questions couldn't be answered at all |
| B5 | Typo-proof search (plus Handsome Dan → bulldog) | Agent / backend | "hoddie", "saybrok" or "Handsome Dan" found nothing |

---

## F1: Flight search and filters (front end)

**What I added:** a search bar and filters at the top of the **Products** page (`frontend/src/pages/Products.tsx`):
- **Search box ("Search the hangar")** matches names, fun names, garment types, colors and design tags. Every word must match, e.g. "navy hockey".
- **Category chips:** Hoodies, Crewnecks, Tees, Quarter-zips, Fleece & jackets, Long-sleeve & more. These map the catalogue's 22 messy garment labels into six clean groups.
- **💸 Under $40** value chip, for students on a budget.
- **"In stock in [size]"** picker. It hides anything sold out in your size.
- A live count ("18 of 102 items match"), a **Clear filters** link, and a friendly **"📡 No contacts on radar"** message that points shoppers to Chloe when nothing matches.

**Why it helps a Campus Customs shopper:**
- Finding gear goes from scrolling 102 cards to one tap or a few letters. A Saybrook student types "saybrook" and sees their 3 items.
- The size filter stops the most frustrating moment in apparel shopping: falling for something that's sold out in your size. 145 of 612 size slots are currently sold out.
- The Under $40 chip gives budget-minded students a lane of 25 tees.
- **For the business:** less hunting means more shoppers reach an item page, and the empty-search message turns a dead end into a chat with Chloe.

**See it:** Products page → type "bulldog" (18 match), tap **Hoodies** (27), tap **Under $40** + choose **XL** (15, all under $40), type "pink shorts" (no-contacts message).
**Evidence:** `output/screenshots/p9_F1_flight_search_bulldog.jpg`

---

## F5: Phone-friendly flight menu (front end)

**What I added:** on screens narrower than 760px (`NavBar.tsx` + CSS):
- The five nav links fold behind a **"☰ Flight menu"** button.
- The banner and logo shrink.
- The menu drops down as large, easy-to-tap buttons and **closes itself after every page change**.
- On desktop nothing changes; all links stay visible.

**Why it helps a Campus Customs shopper:**
- Most students shop on their phones. Before, the header took about 300px, so shoppers saw the menu instead of the merch.
- Now the header is **54px**, and products are visible right away.
- Big tap targets mean fewer mis-taps, and the auto-closing menu means no extra tap to get it out of the way.
- The required nav (Home, Products, About Us, Log In, Create Account) is still one tap away.

**See it:** open the site at phone width (or the browser's mobile view) → header shows **YALE Campus Customs** + **☰ Flight menu** → tap it → five big buttons → pick **About Us** and the menu closes.
**Evidence:** `output/screenshots/p9_F5_phone_flight_menu.jpg`

---

## B3: One-shot filter search for Chloe (agent / backend)

**What I added:** a new agent tool, **`search_catalogue`** (`backend/tools.py`). It returns every product matching **all** of these at once:
- `category` (hoodie, crewneck, tee, quarter-zip, fleece / jacket, full-zip hoodie, long-sleeve, mockneck; typos accepted)
- `max_price` / `min_price`
- `color` ("grey" is treated as "gray"; "navy" matches "navy blue")
- `size_in_stock`
- `keywords` (a college, sport or design)
- `sort` (`price_low`, `price_high`, `name`)

Each hit includes the database price, colors and sizes in stock. New return types are `CatalogueHit` and `CatalogueSearch` in `models.py`. It's wired into the agent, its results can become radar cards, and the "must call the tools" check accepts it as a source for prices and stock. The `prompt.md` tool table tells Chloe when to use it.

**Why it helps a Campus Customs shopper:**
- **More accurate:** questions with several conditions ("hoodies under $70 in medium", "cheapest fleece", "navy crewnecks", "tees in XL under $40") are answered from one database query. Before, Chloe had to chain several lookups or couldn't filter at all.
- **Faster and cheaper:** one tool call replaces a search plus a stock and price lookup for each item. Fewer model round-trips means a quicker answer and fewer AI tokens per question.
- **Honest:** prices and sizes come straight from the database, so the radar cards and Chloe's words always agree.

**See it:** ask Chloe "hoodies under $70 that come in medium". She answers from **one** `search_catalogue` call and 8 matching cards appear on radar. Or ask "what's your cheapest fleece?" and the results come sorted by price.
**Evidence (live test):** "Roger, 8 hoodie contacts matching your under-$70, medium criteria are on radar…" with `tools_used: ["search_catalogue"]` and 8 cards.

---

## B5: Typo-proof search, plus Handsome Dan → bulldog (agent / backend)

**What I added:**
- **Typo correction** in `find_products` and `search_catalogue` (`backend/tools.py`). A word the catalogue doesn't know is swapped for its closest catalogue word (Python `difflib`): "hoddie" → hoodie, "crewnek" → crewneck, "saybrok" → saybrook, "franklen" → franklin, "quater" → quarter.
- **A safety guard:** a real word is never "fixed" into a shorter or longer one. "Shorts" is *not* turned into "short" (from short-sleeve), so Chloe never pretends we sell shorts.
- **Handsome Dan understanding:** "Handsome Dan", "mascot" and "bulldogs" all mean **bulldog**, so those searches find our 4 vintage bulldog crewnecks and hoodies.
- The new "Handsome Dan questions" section in `prompt.md` makes Chloe say honestly that there's no merch *named* Handsome Dan, then show the bulldog designs.

**Why it helps a Campus Customs shopper:**
- Shoppers type fast on phones. Before, one typo meant "we don't carry that" and a lost sale. Now Chloe finds the right item anyway.
- "Handsome Dan" was the most-asked thing we "didn't have" in the chat logs (see `output/shopper_insights.md`), even though every page shows Dan. Now those shoppers get real bulldog products instead of a dead end.
- **Safer and more accurate:** the shorts guard and the honest Dan wording mean typo-fixing never invents products.

**See it:** ask Chloe "do you have a saybrok crewnek in large?" → "the Saybrook College Crewneck is available in large, only 2 left" (database L = 2). Or ask "anything with handsome dan on it?" → "Negative on products named Handsome Dan, but I've got 4 bulldog-design contacts on radar" with 4 cards.
**Evidence (live tests):** both answers above; "pink shorts" and "gym shorts" still correctly return nothing.
