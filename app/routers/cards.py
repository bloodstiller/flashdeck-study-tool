import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Card, Tag
from app.schemas import CardOut, CardCreate, CardUpdate, ImportResult, ScanResult
from parsers import parse_file

router = APIRouter(prefix="/api/cards", tags=["cards"])

CARDS_DIR = os.environ.get("CARDS_DIR", "/cards")


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_or_create_tag(db: Session, name: str) -> Tag:
    tag = db.query(Tag).filter(Tag.name == name.lower()).first()
    if not tag:
        tag = Tag(name=name.lower())
        db.add(tag)
        db.flush()
    return tag


def ingest_parsed_cards(db: Session, parsed_cards, source_file: str) -> tuple[int, int]:
    """Insert parsed cards into the DB, skipping duplicates by question text."""
    imported = skipped = 0
    for pc in parsed_cards:
        exists = db.query(Card).filter(Card.question == pc.question).first()
        if exists:
            skipped += 1
            continue
        card = Card(question=pc.question, answer=pc.answer, source_file=source_file)
        for tag_name in pc.tags:
            card.tags.append(get_or_create_tag(db, tag_name))
        db.add(card)
        imported += 1
    db.commit()
    return imported, skipped


# ── List / Search ──────────────────────────────────────────────────────────────

@router.get("", response_model=list[CardOut])
def list_cards(
    tag:    Optional[str] = Query(None),
    hard:   bool          = Query(False, description="Only cards marked hard at least once"),
    pinned: bool          = Query(False, description="Only pinned cards"),
    unseen: bool          = Query(False, description="Only cards never studied"),
    q:      Optional[str] = Query(None, description="Search question text"),
    skip:   int           = Query(0, ge=0),
    limit:  int           = Query(200, le=500),
    db:     Session       = Depends(get_db),
):
    query = db.query(Card)
    if tag:
        query = query.join(Card.tags).filter(Tag.name == tag.lower())
    if hard:
        query = query.filter(Card.times_hard > 0)
    if pinned:
        query = query.filter(Card.pinned == True)
    if unseen:
        query = query.filter(Card.times_seen == 0)
    if q:
        query = query.filter(Card.question.ilike(f"%{q}%"))
    return query.offset(skip).limit(limit).all()


# ── Create card ───────────────────────────────────────────────────────────────

@router.post("", response_model=CardOut, status_code=201)
def create_card(body: CardCreate, db: Session = Depends(get_db)):
    card = Card(
        question=body.question,
        answer=body.answer,
        notes=body.notes,
        source_file="Manual",
    )
    for tag_name in (body.tags or []):
        card.tags.append(get_or_create_tag(db, tag_name))
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


# ── Due today queue ────────────────────────────────────────────────────────────

@router.get("/due-today", response_model=list[CardOut])
def due_today(db: Session = Depends(get_db)):
    """Cards due for review today (SM-2 due_date <= now, or never seen)."""
    now = datetime.now(timezone.utc)
    return (
        db.query(Card)
        .filter(
            (Card.due_date <= now) |
            (Card.due_date == None)  # noqa: E711
        )
        .order_by(Card.due_date.asc().nullsfirst())
        .all()
    )


# ── Folder listing + stats ────────────────────────────────────────────────────

@router.get("/folders", response_model=list[dict])
def list_folders(db: Session = Depends(get_db)):
    """Return each unique source folder with card stats."""
    cards = db.query(Card).all()
    folders: dict[str, dict] = {}
    for card in cards:
        folder = _card_folder(card)
        if folder not in folders:
            folders[folder] = {"folder": folder, "total": 0, "seen": 0,
                               "hard": 0, "pinned": 0, "correct": 0}
        s = folders[folder]
        s["total"]   += 1
        s["hard"]    += 1 if card.times_hard   > 0 else 0
        s["pinned"]  += 1 if card.pinned else 0
        s["seen"]    += 1 if card.times_seen   > 0 else 0
        s["correct"] += card.times_correct
    # compute confidence %
    for s in folders.values():
        s["pct_confident"] = round(s["correct"] / s["seen"] * 100, 1) if s["seen"] else 0.0
    return sorted(folders.values(), key=lambda x: x["folder"])


def _card_folder(card: Card) -> str:
    if card.source_file:
        # normalise both Windows and POSIX separators
        normalised = card.source_file.replace(chr(92), "/")
        parts = normalised.split("/")
        if len(parts) > 1:
            return parts[0]
    return "Uncategorised"


# ── Single card ────────────────────────────────────────────────────────────────

@router.get("/{card_id}", response_model=CardOut)
def get_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    return card


@router.patch("/{card_id}", response_model=CardOut)
def update_card(card_id: int, body: CardUpdate, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    if body.question is not None:
        card.question = body.question
    if body.answer is not None:
        card.answer = body.answer
    if body.notes is not None:
        card.notes = body.notes
    if body.tags is not None:
        card.tags = [get_or_create_tag(db, t) for t in body.tags]
    db.commit()
    db.refresh(card)
    return card


@router.delete("/{card_id}", status_code=204)
def delete_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    db.delete(card)
    db.commit()


# ── Create card ───────────────────────────────────────────────────────────────

@router.post("", response_model=CardOut, status_code=201)
def create_card(body: CardCreate, db: Session = Depends(get_db)):
    card = Card(
        question=body.question,
        answer=body.answer,
        notes=body.notes,
        source_file="Manual",
    )
    for tag_name in (body.tags or []):
        card.tags.append(get_or_create_tag(db, tag_name))
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


# ── Due today queue ────────────────────────────────────────────────────────────

@router.get("/due-today", response_model=list[CardOut])
def due_today(db: Session = Depends(get_db)):
    """Cards due for review today (SM-2 due_date <= now, or never seen)."""
    now = datetime.now(timezone.utc)
    return (
        db.query(Card)
        .filter(
            (Card.due_date <= now) |
            (Card.due_date == None)  # noqa: E711
        )
        .order_by(Card.due_date.asc().nullsfirst())
        .all()
    )


# ── Folder listing + stats ────────────────────────────────────────────────────

# ── Pin / unpin ────────────────────────────────────────────────────────────────

@router.post("/{card_id}/pin", response_model=CardOut)
def toggle_pin(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    card.pinned = not card.pinned
    db.commit()
    db.refresh(card)
    return card


# ── Reset hard counter ─────────────────────────────────────────────────────────

@router.post("/{card_id}/reset-hard", response_model=CardOut)
def reset_hard(card_id: int, db: Session = Depends(get_db)):
    """Mark the user as confident — zeroes hard counter."""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(404, "Card not found")
    card.times_hard = 0
    db.commit()
    db.refresh(card)
    return card


# ── File upload import ─────────────────────────────────────────────────────────

@router.post("/import", response_model=ImportResult)
async def import_files(
    files: list[UploadFile] = File(...),
    db:    Session          = Depends(get_db),
):
    total_imported = total_skipped = 0
    errors: list[str] = []
    all_cards: list[Card] = []

    for upload in files:
        if not (upload.filename.endswith(".md") or upload.filename.endswith(".txt")):
            errors.append(f"{upload.filename}: unsupported file type")
            continue
        try:
            content = (await upload.read()).decode("utf-8", errors="replace")
            parsed = parse_file(content)
            if not parsed:
                errors.append(f"{upload.filename}: no cards found")
                continue
            imp, skp = ingest_parsed_cards(db, parsed, upload.filename)
            total_imported += imp
            total_skipped  += skp
        except Exception as e:
            errors.append(f"{upload.filename}: {e}")

    # Return freshly imported cards
    recent = (
        db.query(Card)
        .order_by(Card.created_at.desc())
        .limit(total_imported)
        .all()
    )
    return ImportResult(
        imported=total_imported,
        skipped=total_skipped,
        errors=errors,
        cards=recent,
    )


# ── Folder scan (server-side) ──────────────────────────────────────────────────

@router.post("/scan", response_model=ScanResult)
def scan_cards_dir(db: Session = Depends(get_db)):
    """
    Recursively scan the CARDS_DIR volume for .md files and import them.
    Mount your notes folder to /cards in docker-compose.
    """
    cards_path = Path(CARDS_DIR)
    if not cards_path.exists():
        raise HTTPException(400, f"Cards directory not found: {CARDS_DIR}")

    md_files = list(cards_path.rglob("*.md")) + list(cards_path.rglob("*.txt"))
    if not md_files:
        return ScanResult(files_found=0, imported=0, skipped=0, errors=[])

    total_imported = total_skipped = 0
    errors: list[str] = []

    for path in md_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            parsed  = parse_file(content)
            if not parsed:
                continue
            imp, skp = ingest_parsed_cards(db, parsed, str(path.relative_to(cards_path)))
            total_imported += imp
            total_skipped  += skp
        except Exception as e:
            errors.append(f"{path.name}: {e}")

    return ScanResult(
        files_found=len(md_files),
        imported=total_imported,
        skipped=total_skipped,
        errors=errors,
    )


# ── Export all cards as markdown zip ──────────────────────────────────────────

@router.get("/export")
def export_cards(db: Session = Depends(get_db)):
    """
    Export all cards as a zip of .md files, preserving folder structure.
    Each file uses the noteId frontmatter format so it can be re-imported.
    """
    import io
    import zipfile
    import re
    from fastapi.responses import StreamingResponse

    cards = db.query(Card).order_by(Card.source_file, Card.id).all()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        used_paths: set[str] = set()

        for card in cards:
            # Build folder path from source_file
            if card.source_file and card.source_file != "Manual":
                # source_file is like "Current Technology/What is SQL injection.md"
                # Use its directory but derive filename from question
                folder = "/".join(card.source_file.replace("\\", "/").split("/")[:-1])
            else:
                folder = "Manual"

            # Derive a safe filename from the question
            safe = re.sub(r'[^\w\s-]', '', card.question)[:60].strip()
            safe = re.sub(r'\s+', '_', safe)
            path = f"FlashDeck_Export/{folder}/{safe}.md" if folder else f"FlashDeck_Export/{safe}.md"

            # Avoid collisions
            base, ext = path.rsplit(".", 1)
            counter = 1
            while path in used_paths:
                path = f"{base}_{counter}.{ext}"
                counter += 1
            used_paths.add(path)

            # Build noteId-style markdown
            lines = [
                "---",
                f"noteId: {card.id}",
                "---",
                "",
                card.question,
                "",
                "---",
                "",
                card.answer,
            ]
            if card.notes:
                lines += ["", "<!-- notes -->", card.notes]

            zf.writestr(path, "\n".join(lines))

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=flashdeck_export.zip"},
    )
