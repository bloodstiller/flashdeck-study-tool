from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import os
import logging

from sqlalchemy import text
from app.database import Base, engine, SessionLocal
from app.routers import cards, study, resources
from app.services.seed import seed_resources

logger = logging.getLogger("flashdeck")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Migrations: add columns if they don't exist (safe to run every boot)
    migrations = [
        ("ALTER TABLE cards ADD COLUMN pinned BOOLEAN DEFAULT 0",         "pinned"),
        ("ALTER TABLE cards ADD COLUMN notes TEXT",                        "notes"),
        ("ALTER TABLE cards ADD COLUMN due_date DATETIME",                 "due_date"),
        ("ALTER TABLE cards ADD COLUMN interval_days INTEGER DEFAULT 1",   "interval_days"),
        ("ALTER TABLE cards ADD COLUMN ease_factor REAL DEFAULT 2.5",      "ease_factor"),
        ("ALTER TABLE cards ADD COLUMN last_reviewed DATETIME",            "last_reviewed"),
    ]
    with engine.connect() as conn:
        for sql, col in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"Migration: added '{col}' column to cards table")
            except Exception:
                pass  # Column already exists

    db = SessionLocal()
    try:
        # Seed bundled resources if the DB is fresh
        res_count = seed_resources(db)
        if res_count:
            logger.info(f"Seeded {res_count} resources from resources_seed.md")

        # Auto-import bundled CSTM cards on first run
        from app.models import Card
        if db.query(Card).count() == 0:
            from pathlib import Path
            from parsers.markdown import parse_file
            from app.routers.cards import ingest_parsed_cards
            cards_dir = Path(os.environ.get("CARDS_DIR", "/app/cards"))
            if cards_dir.exists():
                md_files = list(cards_dir.rglob("*.md"))
                total_imp = total_skp = 0
                for path in md_files:
                    try:
                        parsed = parse_file(path.read_text(encoding="utf-8", errors="replace"))
                        imp, skp = ingest_parsed_cards(db, parsed, str(path.relative_to(cards_dir)))
                        total_imp += imp
                        total_skp += skp
                    except Exception as e:
                        logger.warning(f"Could not import {path.name}: {e}")
                if total_imp:
                    logger.info(f"Auto-imported {total_imp} bundled cards from {len(md_files)} files")
    finally:
        db.close()

    yield


app = FastAPI(
    title="FlashDeck",
    description="Adaptive flashcard study tool with multi-source resource discovery",
    version="2.1.0",
    lifespan=lifespan,
)

app.include_router(cards.router)
app.include_router(study.router)
app.include_router(resources.router)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok", "version": app.version}
