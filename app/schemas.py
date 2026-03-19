from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


# ── Tags ─────────────────────────────────────────────────────────────────────

class TagOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


# ── Cards ─────────────────────────────────────────────────────────────────────

class CardOut(BaseModel):
    id:            int
    question:      str
    answer:        str
    source_file:   Optional[str]
    pinned:        bool
    notes:         Optional[str]
    times_seen:    int
    times_correct: int
    times_hard:    int
    difficulty_score: float
    due_date:      Optional[datetime]
    interval_days: int
    ease_factor:   float
    last_reviewed: Optional[datetime]
    tags:          list[TagOut]
    created_at:    datetime
    model_config = {"from_attributes": True}


class CardCreate(BaseModel):
    question: str
    answer:   str
    notes:    Optional[str] = None
    tags:     Optional[list[str]] = []


class CardUpdate(BaseModel):
    question:   Optional[str] = None
    answer:     Optional[str] = None
    notes:      Optional[str] = None
    tags:       Optional[list[str]] = None


# ── Import ────────────────────────────────────────────────────────────────────

class ImportResult(BaseModel):
    imported:   int
    skipped:    int
    errors:     list[str]
    cards:      list[CardOut]


class ScanResult(BaseModel):
    files_found: int
    imported:    int
    skipped:     int
    errors:      list[str]


# ── Resources ─────────────────────────────────────────────────────────────────

class ResourceOut(BaseModel):
    id:          int
    topic:       str
    title:       str
    url:         str
    description: Optional[str]
    model_config = {"from_attributes": True}


class ResourceCreate(BaseModel):
    topic:       str
    title:       str
    url:         str
    description: Optional[str] = None


# ── Study Sessions ────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    mode: str = "all"   # all | hard | tag:<name>


class SessionOut(BaseModel):
    id:         int
    started_at: datetime
    ended_at:   Optional[datetime]
    mode:       str
    total:      int
    got:        int
    hard:       int
    skipped:    int
    model_config = {"from_attributes": True}


class RecordResult(BaseModel):
    card_id: int
    result:  str   # got | hard | skip


class CardResultOut(BaseModel):
    id:          int
    card_id:     int
    result:      str
    answered_at: datetime
    model_config = {"from_attributes": True}


# ── Folder / category stats ──────────────────────────────────────────────────────

class FolderStats(BaseModel):
    folder:        str
    total:         int
    seen:          int
    hard:          int
    pinned:        int
    correct:       int
    pct_confident: float   # times_correct / times_seen for seen cards

# ── Weak spots ───────────────────────────────────────────────────────────────────

class WeakSpot(BaseModel):
    card:       CardOut
    hard_count: int
    model_config = {"from_attributes": True}


# ── Forecast ──────────────────────────────────────────────────────────────────────

class ForecastOut(BaseModel):
    due_today:       int
    overdue:         int
    avg_daily_cards: float
    days_to_clear:   Optional[int]
    total_due:       int


# ── Stats ─────────────────────────────────────────────────────────────────────

class DeckStats(BaseModel):
    total_cards:    int
    total_sessions: int
    hard_cards:     int
    pinned_cards:   int
    unseen_cards:   int
    tags:           list[str]
