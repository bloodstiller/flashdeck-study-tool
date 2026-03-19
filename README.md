# FlashDeck

An adaptive flashcard study tool built with FastAPI and SQLite, served locally via Docker. Currently configured with a bundled deck for the **CSTM (Cyber Scheme Team Member)** exam, but can be used for any subject — just swap in your own markdown files.

---

## Quick Start

```bash
git clone <your-repo> flashdeck
cd flashdeck
docker compose up --build
```

Open **http://localhost:8000** — the bundled CSTM deck (126 cards across 6 topic areas) and curated security resources load automatically on first boot.

---

## What It Does

- **Adaptive study** using a simplified SM-2 spaced repetition algorithm — cards you find hard come back sooner, cards you know well are spaced further apart
- **Multiple study modes** — All Cards (weighted), Due Today, Hard Cards, Pinned Cards, Unseen, or by individual topic folder
- **Pin system** — pin any card during study to build a custom review list
- **Per-topic mastery tracking** with trend indicators (improving / declining / stable) based on your last 7 days of results. Mastery starts at 0% and only increases as you study
- **Forecast** — shows how many cards are due today, how many are overdue, and estimates days to clear your review queue at your current study pace
- **End-of-session weak spots** — highlights cards you marked hard more than once in a single session
- **Streak counter** — tracks consecutive correct answers during study
- **Navigation** — move back and forward through cards you've already seen, redo a card immediately, or re-insert it at a random position later in the queue
- **Inline editing** — edit any card's question, answer, or notes without leaving the study view
- **Create cards** directly in the app, no file editing required
- **Export** — download all cards as a zip of `.md` files, preserving folder structure and including any edits or notes you've added. Safe to re-import
- **Curated resources** that surface automatically when you mark a card as hard, matched to the card's topic
- **Resource generation** — bundled seed resources included; optionally supplement with DuckDuckGo search, a local Ollama model, or the Anthropic Claude API

---

## Project Structure

```
flashdeck/
├── app/
│   ├── main.py              # FastAPI entry point, startup migrations, auto-import
│   ├── database.py          # SQLAlchemy engine and session factory
│   ├── models.py            # ORM models: Card, Tag, Resource, StudySession, CardResult
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── resources_seed.md    # Bundled curated security resource links (48 topics, 158 links)
│   ├── routers/
│   │   ├── cards.py         # Card CRUD, create, import, folder scan, pin, export, due-today
│   │   ├── study.py         # Sessions, SM-2 result recording, queues, stats, forecast, mastery
│   │   └── resources.py     # Resource management, DDG search, Ollama, Claude generation
│   └── services/
│       ├── sm2.py           # SM-2 spaced repetition algorithm and weighted sort
│       ├── seed.py          # Bundled resource loader
│       ├── ddg.py           # DuckDuckGo search (no API key required)
│       └── ollama.py        # Local Ollama LLM integration
├── parsers/
│   └── markdown.py          # Markdown card parser (all supported formats)
├── static/
│   ├── css/style.css
│   └── js/
│       ├── api.js           # REST API client
│       ├── study.js         # Study session controller (SM-2, nav, redo, edit, streak)
│       └── app.js           # Page routing, topics, forecast, card management
├── templates/
│   └── index.html           # Single-page application shell
├── cards/                   # Bundled CSTM flashcard deck (auto-imported on first boot)
│   ├── Current Technology/
│   ├── Mitigation/
│   ├── Networking/
│   ├── Older Technology/
│   ├── Protocols/
│   └── Scope-Laws-Risk/
├── tests/
│   └── test_parser.py       # Parser unit tests
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Importing Your Own Cards

FlashDeck supports three import methods.

### Upload via the browser

Go to **Import → Select Files** and pick one or more `.md` files (hold `Ctrl`/`Cmd` to select multiple), or use **Select Folder** to import an entire directory recursively. Duplicate cards are skipped automatically on every import.

### Mount a folder (recommended for large collections)

Edit `docker-compose.yml` and uncomment the extra-cards volume:

```yaml
volumes:
  - /path/to/your/notes:/extra-cards:ro
```

Then click **Scan Mounted /cards Folder** on the Import page. The server walks the full directory tree and imports every `.md` file it finds.

### Supported card formats

**One card per file** (Obsidian / note-taking app format):
```markdown
---
noteId: 1234567890
---

What is SQL injection?

---

A vulnerability where malicious SQL is injected through user-controlled
input to manipulate or access a database.
```

**Inline — one card per line:**
```
What is SQL injection?  ---  Injecting malicious SQL via user input.
What is a reverse shell?  ---  The victim connects back to the attacker.
```

**Heading blocks — multiple cards per file:**
```markdown
## What is SQL injection?

A vulnerability where malicious SQL is injected via user input.

**Tags:** web, sqli

---

## What is XSS?

Injecting malicious scripts into pages viewed by other users.

**Tags:** web, xss
```

---

## Exporting Cards

All edits, notes, and newly created cards are saved to the SQLite database inside the Docker volume, not back to your original `.md` files. To back up your changes, click **⬇ Export Cards** on the All Cards page.

This downloads a zip of `.md` files in the `noteId` frontmatter format, preserving the original folder structure. Cards created manually in the app are exported to a `Manual/` folder. The export can be re-imported directly if you ever need to restore from scratch.

**When to export:**
- After editing cards or adding notes
- Before running `docker volume rm flashdeck-data`
- As a regular backup alongside your original source files

---

## Study Modes

| Mode | Description |
|------|-------------|
| **Study All** | Full deck, weighted by SM-2 priority (overdue → new → future) |
| **Study Due** | Only cards due for review today |
| **Study Hard** | Cards marked hard at least once, sorted by difficulty |
| **Study Pinned** | Your custom pinned list |
| **Study Unseen** | Cards you have never reviewed |
| **Topic — Study All** | All cards in one folder, SM-2 weighted |
| **Topic — Due** | Due cards within a specific topic |
| **Topic — Hard Only** | Hard cards within a specific topic |

---

## Keyboard Shortcuts

All shortcuts are active on the study screen. Press `?` from anywhere in the app to show this list. Shortcuts are automatically suppressed when typing in any input field or textarea.

| Key | Action |
|-----|--------|
| `Space` / `Enter` | Flip card |
| `G` | Got it |
| `H` | Hard |
| `S` | Skip |
| `N` | Redo now — re-flip this card immediately |
| `L` | Redo later — re-insert at a random position in the queue |
| `P` | Pin / unpin |
| `E` | Edit card inline |
| `R` | Open resource panel |
| `←` | Previous card |
| `→` | Next card |
| `?` | Keyboard shortcut help |

---

## Spaced Repetition

FlashDeck uses a simplified SM-2 algorithm. Every result updates the card's schedule:

| Result | Effect |
|--------|--------|
| **Got it** | Interval multiplied by ease factor (starts at 1d → 6d → grows) |
| **Hard** | Interval resets to 1 day; ease factor reduced |
| **Skip** | No schedule change |

Cards are sorted for study with overdue cards first, then unseen cards, then cards due in the future. Within each group, harder cards come first.

Mastery scores on the Topics page start at 0% for unstudied topics and increase as you study. Mastery is calculated as the proportion of cards answered correctly across the entire folder — unseen cards count against the score until you review them.

---

## Resources

Resources are links matched to card topics. They surface automatically in a panel when you mark a card as hard.

### Bundled seed (always available, no internet required)

48 pre-curated security topics with 158 links are bundled in `app/resources_seed.md` and loaded automatically on first boot. Topics include pass-the-hash, Active Directory, Kerberos, SQL injection, XSS, CSRF, SSL/TLS vulnerabilities (Heartbleed, POODLE, BEAST, CRIME, DROWN, ROBOT), privilege escalation, UK law (CMA, GDPR, RIPA, PJA), NCSC CHECK, and more — matched specifically to the CSTM exam syllabus.

### Additional generation methods

From the **Import** page, you can supplement the seed with:

| Method | Requires | Notes |
|--------|----------|-------|
| **Bundled Seed** | Nothing | Always available, pre-curated for CSTM |
| **DuckDuckGo Search** | Internet | No API key, finds resources based on card topics |
| **Ollama (local LLM)** | Ollama running | Fully offline, see Ollama setup below |
| **Claude API** | `ANTHROPIC_API_KEY` | Highest quality, analyses your actual cards |

All methods are **additive** — they never remove existing resources, only add new ones.

---

## Configuration

All configuration is via environment variables in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PATH` | `/data/flashdeck.db` | SQLite database path inside the container |
| `CARDS_DIR` | `/app/cards` | Directory scanned by the server-side folder scan |
| `ANTHROPIC_API_KEY` | *(unset)* | Required only for Claude resource generation |
| `OLLAMA_HOST` | `http://ollama:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `llama3` | Model to use for resource generation |

---

## Ollama Setup (optional)

To use a local LLM for resource generation:

```bash
# Start Ollama alongside FlashDeck
docker compose --profile ollama up -d

# Pull a model (do this once)
docker exec flashdeck-ollama ollama pull llama3

# Then uncomment in docker-compose.yml:
# OLLAMA_HOST:  http://ollama:11434
# OLLAMA_MODEL: llama3
```

GPU support is available — see the commented `deploy` section in `docker-compose.yml`.

---

## REST API

Full interactive documentation is available at **http://localhost:8000/docs** (Swagger UI).

Key endpoint groups:

```
# Cards
GET    /api/cards                        List / search cards
POST   /api/cards                        Create a new card
GET    /api/cards/folders                Folder list with stats
GET    /api/cards/due-today              Cards due for review
GET    /api/cards/export                 Download all cards as a zip of .md files
POST   /api/cards/import                 Upload .md files
POST   /api/cards/scan                   Scan mounted /cards directory
POST   /api/cards/{id}/pin               Toggle pin
POST   /api/cards/{id}/reset-hard        Mark as confident (clear hard count)
PATCH  /api/cards/{id}                   Update question / answer / notes / tags

# Sessions
POST   /api/sessions                     Create study session
POST   /api/sessions/{id}/results        Record a result (triggers SM-2)
POST   /api/sessions/{id}/end            End session
GET    /api/sessions/{id}/weak-spots     Cards hard 2+ times this session
GET    /api/sessions/stats/deck          Deck-wide statistics
GET    /api/sessions/stats/forecast      Review queue forecast
GET    /api/sessions/stats/mastery       Per-topic mastery with trend
GET    /api/sessions/queue/due           SM-2 due queue
GET    /api/sessions/queue/weighted      Full deck, SM-2 weighted
GET    /api/sessions/queue/hard          Hard cards by difficulty
GET    /api/sessions/queue/pinned        Pinned cards
GET    /api/sessions/queue/folder/{name} Cards in a specific folder

# Resources
GET    /api/resources                    List all resources
GET    /api/resources/for-card/{id}      Resources matched to a card
POST   /api/resources/seed               Reload bundled resources_seed.md
POST   /api/resources/generate/ddg       Generate via DuckDuckGo
POST   /api/resources/generate/ollama    Generate via Ollama
POST   /api/resources/generate/claude    Generate via Claude API
POST   /api/resources/generate           Auto-select best available method
GET    /api/resources/status             Availability of each method
```

---

## Data Persistence

The SQLite database is stored in the `flashdeck-data` Docker volume and survives container restarts and rebuilds. Edits made to cards in the app are saved to this database — the original `.md` source files are never modified.

**Backup the database:**
```bash
docker cp flashdeck:/data/flashdeck.db ./flashdeck-backup.db
```

**Restore the database:**
```bash
docker cp ./flashdeck-backup.db flashdeck:/data/flashdeck.db
```

**Export cards to markdown** (preserves edits and notes):

Use the **⬇ Export Cards** button on the All Cards page, or hit `GET /api/cards/export` directly.

---

## Running Tests

```bash
cd flashdeck
pip install pytest
pytest tests/ -v
```

---

## Database Migrations

Column additions run automatically on startup via `ALTER TABLE` statements in `main.py`. Existing databases upgrade without requiring a rebuild or data loss. Safe to run on every boot.
