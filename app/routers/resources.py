"""
Resources router.

All generation methods are ADDITIVE — they never wipe existing resources,
they only insert entries whose URL is not already in the database.

Generation methods:
  POST /api/resources/seed              — reload bundled app/resources_seed.md
  POST /api/resources/generate/ddg      — DuckDuckGo search (no key needed)
  POST /api/resources/generate/ollama   — local Ollama LLM
  POST /api/resources/generate/claude   — Anthropic Claude API
  POST /api/resources/generate          — auto-select best available
  GET  /api/resources/status            — availability of each method
"""

import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Resource, Card
from app.schemas import ResourceOut, ResourceCreate
from app.services.ddg import search_topics
from app.services.ollama import generate_resources as ollama_generate, is_available as ollama_available, OllamaError
from app.services.seed import reload_seed, SEED_FILE
from parsers.markdown import parse_resources

router = APIRouter(prefix="/api/resources", tags=["resources"])

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL      = "claude-sonnet-4-20250514"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _save_resources_additive(db: Session, parsed: dict[str, list[dict]]) -> list[Resource]:
    """Insert resources whose URL is not already in the DB. Never deletes."""
    created = []
    for topic, items in parsed.items():
        for item in items:
            exists = db.query(Resource).filter(Resource.url == item["url"]).first()
            if exists:
                continue
            r = Resource(
                topic=topic,
                title=item["title"],
                url=item["url"],
                description=item.get("description", ""),
            )
            db.add(r)
            created.append(r)
    db.commit()
    for r in created:
        db.refresh(r)
    return created


def _extract_topics(cards: list[Card]) -> list[str]:
    tags = set()
    for card in cards:
        for tag in card.tags:
            tags.add(tag.name)
    return list(tags)


# ── Status ─────────────────────────────────────────────────────────────────────

@router.get("/status")
async def generation_status():
    claude_ok          = bool(ANTHROPIC_API_KEY)
    ollama_ok, ol_msg  = await ollama_available()
    seed_exists        = SEED_FILE.exists()
    return {
        "claude": {
            "available": claude_ok,
            "message":   "Ready" if claude_ok else "Set ANTHROPIC_API_KEY in docker-compose.yml",
        },
        "ollama": {
            "available": ollama_ok,
            "message":   ol_msg,
        },
        "ddg": {
            "available": True,
            "message":   "Always available — no API key required",
        },
        "seed": {
            "available": seed_exists,
            "message":   "Bundled curated security resources" if seed_exists else "resources_seed.md not found",
        },
    }


# ── List / CRUD ────────────────────────────────────────────────────────────────

@router.get("", response_model=list[ResourceOut])
def list_resources(topic: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Resource)
    if topic:
        q = q.filter(Resource.topic == topic.lower())
    return q.order_by(Resource.topic, Resource.id).all()


@router.get("/topics", response_model=list[str])
def list_topics(db: Session = Depends(get_db)):
    rows = db.query(Resource.topic).distinct().order_by(Resource.topic).all()
    return [r[0] for r in rows]


@router.get("/for-card/{card_id}", response_model=list[ResourceOut])
def resources_for_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(404, "Card not found")

    card_text = (card.question + " " + card.answer).lower()
    card_tags  = {t.name for t in card.tags}

    all_resources = db.query(Resource).all()
    matched, seen_ids = [], set()

    def add(r):
        if r.id not in seen_ids:
            seen_ids.add(r.id)
            matched.append(r)

    _STOP = {"the", "and", "for", "with", "from", "this", "that", "are", "its", "not"}

    def _topic_matches(topic: str) -> bool:
        phrase = topic.replace("_", " ")
        # 1. Full phrase must appear verbatim (e.g. "pass the hash")
        if phrase in card_text:
            return True
        # 2. ALL significant words (len >= 3, not a stop word) must appear.
        #    Prevents a single common word like "attacks" triggering unrelated topics.
        words = [w for w in phrase.split() if len(w) >= 3 and w not in _STOP]
        return bool(words) and all(w in card_text for w in words)

    # Exact tag match first, then fuzzy
    for r in all_resources:
        if r.topic in card_tags:
            add(r)
    for r in all_resources:
        if _topic_matches(r.topic):
            add(r)

    return matched


@router.post("", response_model=ResourceOut, status_code=201)
def create_resource(body: ResourceCreate, db: Session = Depends(get_db)):
    r = Resource(**body.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@router.delete("/{resource_id}", status_code=204)
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    r = db.query(Resource).filter(Resource.id == resource_id).first()
    if not r:
        raise HTTPException(404, "Resource not found")
    db.delete(r)
    db.commit()


# ── Seed ───────────────────────────────────────────────────────────────────────

@router.post("/seed", response_model=dict)
def load_seed(db: Session = Depends(get_db)):
    """Reload app/resources_seed.md — additive, never removes existing resources."""
    try:
        added = reload_seed(db)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))

    total = db.query(Resource).count()
    return {"added": added, "total": total}


# ── DDG ────────────────────────────────────────────────────────────────────────

@router.post("/generate/ddg", response_model=list[ResourceOut])
async def generate_ddg(db: Session = Depends(get_db)):
    """Search DuckDuckGo by card topics. Additive."""
    cards  = db.query(Card).limit(200).all()
    topics = _extract_topics(cards)

    if not topics:
        topics = [
            "sql_injection", "xss", "csrf", "ssrf", "active_directory",
            "privilege_escalation", "kerberos", "pass_the_hash", "enumeration",
            "ssl_tls", "web_application", "credentials", "shells",
        ]

    search_results = await search_topics(topics, max_per_topic=3)

    parsed: dict[str, list[dict]] = {}
    for topic, results in search_results.items():
        if results:
            parsed[topic] = [
                {"title": r.title, "url": r.url, "description": r.description}
                for r in results
            ]

    if not parsed:
        raise HTTPException(502, "DuckDuckGo returned no usable results")

    return _save_resources_additive(db, parsed)


# ── Ollama ─────────────────────────────────────────────────────────────────────

@router.post("/generate/ollama", response_model=list[ResourceOut])
async def generate_ollama(db: Session = Depends(get_db)):
    """Generate via local Ollama. Additive."""
    cards = db.query(Card).limit(80).all()
    if not cards:
        raise HTTPException(400, "No cards in database")
    try:
        parsed = await ollama_generate(cards)
    except OllamaError as e:
        raise HTTPException(503, str(e))
    return _save_resources_additive(db, parsed)


# ── Claude ─────────────────────────────────────────────────────────────────────

@router.post("/generate/claude", response_model=list[ResourceOut])
async def generate_claude(db: Session = Depends(get_db)):
    """Generate via Anthropic Claude API. Additive."""
    if not ANTHROPIC_API_KEY:
        raise HTTPException(400, "ANTHROPIC_API_KEY not set")

    cards = db.query(Card).limit(80).all()
    if not cards:
        raise HTTPException(400, "No cards in database")

    sample = "\n\n".join(f"Q: {c.question}\nA: {c.answer}" for c in cards)
    prompt = f"""You are a study resource curator for security certification exam prep.

Analyse these flashcard Q&A pairs, identify the key topics, and generate a curated
resources file in EXACTLY this markdown format:

## topic_name
- [Resource Title](https://real-url.com) - One-line description

Rules:
- Lowercase underscore-separated topic names (e.g. pass_the_hash, active_directory)
- 2-4 resources per topic
- REAL URLs only — PortSwigger, HackTricks, OWASP, NIST, GitHub, official docs
- No placeholder or invented URLs
- Return ONLY the markdown, no preamble

FLASHCARDS:
{sample}"""

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={"model": CLAUDE_MODEL, "max_tokens": 1500,
                  "messages": [{"role": "user", "content": prompt}]},
        )

    if resp.status_code != 200:
        raise HTTPException(502, f"Claude API error: {resp.text}")

    text   = resp.json()["content"][0]["text"]
    parsed = parse_resources(text)
    if not parsed:
        raise HTTPException(502, "Claude returned no parseable resources")

    return _save_resources_additive(db, parsed)


# ── Auto ───────────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=dict)
async def generate_auto(db: Session = Depends(get_db)):
    """Auto-select best available method. Always seeds first as baseline."""
    # Always top up from seed file
    try:
        seed_added = reload_seed(db)
    except FileNotFoundError:
        seed_added = 0

    method    = "seed_only"
    generated = 0
    message   = ""

    if ANTHROPIC_API_KEY:
        try:
            result    = await generate_claude(db)
            generated = len(result)
            method    = "claude"
            message   = f"Added {generated} resources via Claude"
        except Exception as e:
            message = f"Claude failed ({e}), trying Ollama…"

    if not generated:
        ollama_ok, _ = await ollama_available()
        if ollama_ok:
            try:
                result    = await generate_ollama(db)
                generated = len(result)
                method    = "ollama"
                message   = f"Added {generated} resources via Ollama"
            except Exception as e:
                message = f"Ollama failed ({e}), trying DuckDuckGo…"

    if not generated:
        try:
            result    = await generate_ddg(db)
            generated = len(result)
            method    = "ddg"
            message   = f"Found {generated} resources via DuckDuckGo"
        except Exception as e:
            message = f"DuckDuckGo also failed ({e})"

    if not generated and seed_added:
        message = f"Loaded {seed_added} bundled resources"
        method  = "seed"

    total = db.query(Resource).count()
    return {"method": method, "generated": generated, "seed": seed_added, "total": total, "message": message}
