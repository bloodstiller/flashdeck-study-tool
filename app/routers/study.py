from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models import Card, Tag, StudySession, CardResult
from app.schemas import (
    SessionCreate, SessionOut, RecordResult, CardResultOut,
    DeckStats, CardOut, WeakSpot, ForecastOut
)
from app.services.sm2 import apply_sm2, weighted_sort

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# ── Create session ─────────────────────────────────────────────────────────────

@router.post("", response_model=SessionOut)
def create_session(body: SessionCreate, db: Session = Depends(get_db)):
    session = StudySession(mode=body.mode)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


# ── Get / list sessions ────────────────────────────────────────────────────────

@router.get("", response_model=list[SessionOut])
def list_sessions(limit: int = 20, db: Session = Depends(get_db)):
    return (
        db.query(StudySession)
        .order_by(StudySession.started_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: int, db: Session = Depends(get_db)):
    s = db.query(StudySession).filter(StudySession.id == session_id).first()
    if not s:
        raise HTTPException(404, "Session not found")
    return s


# ── Record a card result ───────────────────────────────────────────────────────

@router.post("/{session_id}/results", response_model=CardResultOut)
def record_result(
    session_id: int,
    body:       RecordResult,
    db:         Session = Depends(get_db),
):
    session = db.query(StudySession).filter(StudySession.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")

    card = db.query(Card).filter(Card.id == body.card_id).first()
    if not card:
        raise HTTPException(404, "Card not found")

    if body.result not in ("got", "hard", "skip"):
        raise HTTPException(400, "result must be: got, hard, or skip")

    # Persist result
    result_row = CardResult(session_id=session_id, card_id=body.card_id, result=body.result)
    db.add(result_row)

    # Update card aggregate counters
    card.times_seen += 1
    if body.result == "got":
        card.times_correct += 1
    elif body.result == "hard":
        card.times_hard += 1

    # Apply SM-2 scheduling
    apply_sm2(card, body.result)

    db.commit()
    db.refresh(result_row)
    return result_row


# ── End session ────────────────────────────────────────────────────────────────

@router.post("/{session_id}/end", response_model=SessionOut)
def end_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(StudySession).filter(StudySession.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    session.ended_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session


# ── Weak spots for a session ───────────────────────────────────────────────────

@router.get("/{session_id}/weak-spots", response_model=list[WeakSpot])
def session_weak_spots(session_id: int, db: Session = Depends(get_db)):
    """Cards marked hard 2+ times within this session."""
    results = (
        db.query(CardResult.card_id, func.count(CardResult.id).label("hard_count"))
        .filter(CardResult.session_id == session_id, CardResult.result == "hard")
        .group_by(CardResult.card_id)
        .having(func.count(CardResult.id) >= 2)
        .order_by(func.count(CardResult.id).desc())
        .all()
    )
    spots = []
    for card_id, hard_count in results:
        card = db.query(Card).filter(Card.id == card_id).first()
        if card:
            spots.append(WeakSpot(card=card, hard_count=hard_count))
    return spots


# ── Deck-wide stats ────────────────────────────────────────────────────────────

@router.get("/stats/deck", response_model=DeckStats)
def deck_stats(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    total_cards    = db.query(Card).count()
    total_sessions = db.query(StudySession).count()
    hard_cards     = db.query(Card).filter(Card.times_hard > 0).count()
    pinned_cards   = db.query(Card).filter(Card.pinned == True).count()  # noqa: E712
    unseen_cards   = db.query(Card).filter(Card.times_seen == 0).count()
    tags           = [t.name for t in db.query(Tag).order_by(Tag.name).all()]
    return DeckStats(
        total_cards=total_cards,
        total_sessions=total_sessions,
        hard_cards=hard_cards,
        pinned_cards=pinned_cards,
        unseen_cards=unseen_cards,
        tags=tags,
    )


# ── Hard cards queue (weighted by difficulty) ──────────────────────────────────

@router.get("/queue/hard", response_model=list[CardOut])
def hard_queue(db: Session = Depends(get_db)):
    cards = db.query(Card).filter(Card.times_hard > 0).all()
    return weighted_sort(cards)


# ── Pinned cards queue ─────────────────────────────────────────────────────────

@router.get("/queue/pinned", response_model=list[CardOut])
def pinned_queue(db: Session = Depends(get_db)):
    cards = db.query(Card).filter(Card.pinned == True).order_by(Card.id).all()  # noqa: E712
    return weighted_sort(cards)


# ── Due today queue (SM-2 weighted) ───────────────────────────────────────────

@router.get("/queue/due", response_model=list[CardOut])
def due_queue(db: Session = Depends(get_db)):
    """Cards due for review today, weighted by how overdue and difficulty."""
    now = datetime.now(timezone.utc)
    cards = (
        db.query(Card)
        .filter(
            (Card.due_date <= now) |
            (Card.due_date == None)  # noqa: E711
        )
        .all()
    )
    return weighted_sort(cards)


# ── All cards weighted queue ───────────────────────────────────────────────────

@router.get("/queue/weighted", response_model=list[CardOut])
def weighted_queue(db: Session = Depends(get_db)):
    """All cards sorted by SM-2 priority: overdue first, then new, then future."""
    cards = db.query(Card).all()
    return weighted_sort(cards)


# ── Folder queue ───────────────────────────────────────────────────────────────

@router.get("/queue/folder/{folder_name:path}", response_model=list[CardOut])
def folder_queue(folder_name: str, db: Session = Depends(get_db)):
    cards = (
        db.query(Card)
        .filter(
            (Card.source_file.like(f"{folder_name}/%")) |
            (Card.source_file.like(f"{folder_name}\\%"))
        )
        .order_by(Card.id)
        .all()
    )
    return weighted_sort(cards)


# ── Folder stats ───────────────────────────────────────────────────────────────

@router.get("/stats/folders", response_model=list[dict])
def folder_stats(db: Session = Depends(get_db)):
    from app.routers.cards import list_folders
    return list_folders(db)


# ── Per-topic mastery (current + trend from recent sessions) ───────────────────

@router.get("/stats/mastery", response_model=list[dict])
def mastery_stats(db: Session = Depends(get_db)):
    """
    Per-topic mastery score (0-100) based on card performance.
    Also returns a simple trend: 'up', 'down', or 'stable' based on
    whether recent results in that folder are better or worse than overall.
    """
    from app.routers.cards import _card_folder
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    cards = db.query(Card).all()
    folders: dict[str, dict] = {}

    for card in cards:
        folder = _card_folder(card)
        if folder not in folders:
            folders[folder] = {
                "folder": folder, "total": 0, "seen": 0,
                "mastery": 0.0, "recent_got": 0, "recent_total": 0,
            }
        f = folders[folder]
        f["total"] += 1
        if card.times_seen > 0:
            f["seen"] += 1

    # Get recent results (last 7 days) grouped by card
    recent = (
        db.query(CardResult.card_id, CardResult.result)
        .filter(CardResult.answered_at >= week_ago)
        .all()
    )
    card_folder_map = {c.id: _card_folder(c) for c in cards}
    for card_id, result in recent:
        folder = card_folder_map.get(card_id)
        if folder and folder in folders:
            folders[folder]["recent_total"] += 1
            if result == "got":
                folders[folder]["recent_got"] += 1

    # Compute mastery per folder
    card_map = {c.id: c for c in cards}
    folder_cards: dict[str, list] = {}
    for card in cards:
        f = _card_folder(card)
        folder_cards.setdefault(f, []).append(card)

    result_list = []
    for folder, data in folders.items():
        fc = folder_cards.get(folder, [])
        seen_cards = [c for c in fc if c.times_seen > 0]
        # Mastery is 0 if no cards have ever been studied in this folder
        if not seen_cards:
            mastery = 0.0
        else:
            # Proportion of cards answered correctly on their last attempt
            # Only count cards that have been studied at least once
            mastery = sum(
                min(c.times_correct / c.times_seen, 1.0) for c in seen_cards
            ) / len(fc) * 100  # divide by TOTAL cards so unseen ones count against mastery

        recent_pct = (data["recent_got"] / data["recent_total"] * 100) if data["recent_total"] > 0 else None
        if recent_pct is None:
            trend = "none"
        elif recent_pct > mastery + 5:
            trend = "up"
        elif recent_pct < mastery - 5:
            trend = "down"
        else:
            trend = "stable"

        # Due cards in this folder
        due_count = sum(
            1 for c in fc
            if c.due_date is None or (
                c.due_date.replace(tzinfo=timezone.utc) if c.due_date.tzinfo is None else c.due_date
            ) <= now
        )

        result_list.append({
            "folder":      folder,
            "total":       data["total"],
            "seen":        data["seen"],
            "mastery":     round(mastery, 1),
            "trend":       trend,
            "due_count":   due_count,
        })

    return sorted(result_list, key=lambda x: x["folder"])


# ── Forecast ───────────────────────────────────────────────────────────────────

@router.get("/stats/forecast", response_model=ForecastOut)
def forecast(db: Session = Depends(get_db)):
    """
    Estimate how many days to clear the review queue at current study pace.
    """
    now      = datetime.now(timezone.utc)
    today    = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    # Due today (due_date <= now) and overdue
    due_today_count = db.query(Card).filter(
        (Card.due_date <= now) | (Card.due_date == None)  # noqa: E711
    ).count()

    overdue_count = db.query(Card).filter(
        Card.due_date < today
    ).count()

    total_due = due_today_count

    # Average cards studied per day over last 7 days
    recent_results = db.query(func.count(CardResult.id)).filter(
        CardResult.answered_at >= week_ago,
        CardResult.result != "skip",
    ).scalar() or 0

    avg_daily = recent_results / 7.0

    days_to_clear = None
    if avg_daily > 0 and total_due > 0:
        days_to_clear = max(1, round(total_due / avg_daily))
    elif total_due == 0:
        days_to_clear = 0

    return ForecastOut(
        due_today=due_today_count,
        overdue=overdue_count,
        avg_daily_cards=round(avg_daily, 1),
        days_to_clear=days_to_clear,
        total_due=total_due,
    )
