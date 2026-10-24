# Campus Customs Air: Yale Shop + Chloe the Chatbot (MGT 409, Homework 4)

A Campus Customs storefront with an aviation twist. Shoppers are "pilots", pages are flights, and **Chloe**, a PydanticAI agent, answers from "Yale Tower" in air traffic control radio calls. Every price and stock number she gives comes from the shop's SQLite database.

- **Front end:** React + Vite + TypeScript (`frontend/`)
- **Back end:** FastAPI (`backend/main.py`)
- **Agent:** PydanticAI, four files under `backend/`: `prompts/prompt.md`, `agent.py`, `tools.py`, `models.py`
- **Model:** `gpt-5.6-luna` through the Portkey gateway (set in `.env`)

> Student project for MGT 409. Not the real Campus Customs store.

## 1. Place the data pack (not in this repo)

The database and product images are kept out of git on purpose. Unzip the course data pack (`hw4_data.zip`) into this folder so it looks like this:

```
hw4/
└── data/
    ├── campus_customs.db
    └── products/          # product images referenced by the catalogue
```

On first start, the back end adds the extra columns and tables it needs (pilot rank and callsign, password date, chat history) to your local copy of the database.

## 2. One-time setup

**API key:** copy `.env.example` to `.env` (in `hw4/` or `hw4/backend/`) and fill in your own `PORTKEY_API_KEY`. Never commit `.env`.

**Back end** (Python 3.11+):

```bash
pip install -r requirements.txt
```

**Front end** (Node 18+):

```bash
cd frontend
npm install
```

## 3. Run it (two terminals)

**Terminal 1, back end** (FastAPI + Chloe on port 8000):

```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2, front end** (Vite on port 5173):

```bash
cd frontend
npm run dev
```

Open **http://localhost:5173**. The front end forwards `/api` and `/images` to port 8000.

**Try it:**
- Log in with the course's seeded test user (`test@campuscustoms.yale.edu`), or create a new account.
- Open the chat ("Radio Chloe", bottom right) and ask "what hoodies do you have?" Product cards appear on the page.
- On an item page, ask "is this one in large?" Chloe knows which item "this" is.
- Every chat turn is recorded in `output/audit_trail.json`.

After editing `backend/prompts/prompt.md`, restart the back end; `--reload` only watches `.py` files.

## 4. What's where

```
hw4/
├── AI_prompts.md             # my prompts to my vibe coder, problem by problem
├── requirements.txt          # Python packages for the back end
├── .env.example              # placeholders only
├── .gitignore                # keeps out data/, .env and other secrets
├── README.md
├── frontend/                 # Vite React TypeScript app
├── backend/
│   ├── main.py               # FastAPI app: products, accounts, chat, chat history
│   ├── agent.py              # Chloe: agent loop, honesty check, audit trail
│   ├── models.py             # structured types (RadioCall, ChatDeps, ...)
│   ├── tools.py              # read-only database tools
│   ├── prompts/prompt.md     # Chloe's instructions and safety rules
│   ├── auth.py               # hashed passwords, sessions, schema setup
│   ├── reels.py              # cargo-drop GIF reels for product cards
│   └── product_flair.json    # playful product display names
├── output/
│   ├── harness.md            # how the whole system works
│   ├── design.md             # design choices and why they help customers buy
│   ├── usability.md          # usability improvements
│   ├── app_check.html        # live-site tests with screenshots (double-click to open)
│   ├── app_check_images/     # screenshots linked from app_check.html
│   └── audit_trail.json      # append-only flight recorder of Chloe's agent loop
└── scripts/                  # helper scripts (shopper insights, product flair)
```

Start with `output/harness.md` for the full system manual: model fields, tools, safety rules, loop limits, result caps and the model.

## Credits

- Handsome Dan XIX ("Kingman") photo by Joeshmonobody, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), via [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Handsome_Dan_Kingman.jpg).
- Operation Christmas Drop photos: U.S. Air Force photos by Senior Airman Katrina Brisbin, Senior Airman Natalie Doan and Senior Airman Brooklyn Golightly. Public domain, via Wikimedia Commons (links on the About page).
- Fonts: Playfair Display, Inter, Saira Stencil One and JetBrains Mono, via Google Fonts.
