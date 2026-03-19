"""
Simplified SM-2 spaced repetition algorithm.

Quality mapping (from our Got/Hard results):
  got  → quality 4  (correct, some effort)
  hard → quality 1  (incorrect / very hard)
  skip → no update

SM-2 rules:
  If quality >= 3 (got):
    interval(0) = 1 day
    interval(1) = 6 days
    interval(n) = interval(n-1) * ease_factor
    ease_factor += 0.1 - (5 - quality) * 0.08
  If quality < 3 (hard):
    interval = 1 day
    ease_factor -= 0.2
  ease_factor minimum = 1.3
"""

from datetime import datetime, timezone, timedelta
from app.models import Card


QUALITY_MAP = {
    "got":  4,
    "hard": 1,
    "skip": None,
}


def apply_sm2(card: Card, result: str) -> None:
    """Update card's spaced repetition fields in-place based on study result."""
    quality = QUALITY_MAP.get(result)
    if quality is None:
        return  # skip — don't update scheduling

    now = datetime.now(timezone.utc)
    card.last_reviewed = now

    if quality >= 3:
        # Correct response — extend interval
        if card.times_seen <= 1:
            card.interval_days = 1
        elif card.times_seen == 2:
            card.interval_days = 6
        else:
            card.interval_days = max(1, round(card.interval_days * card.ease_factor))
        # Adjust ease factor (quality 4 keeps it roughly stable)
        card.ease_factor = max(1.3, card.ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    else:
        # Incorrect — reset interval, reduce ease
        card.interval_days = 1
        card.ease_factor = max(1.3, card.ease_factor - 0.2)

    card.due_date = now + timedelta(days=card.interval_days)


def weighted_sort(cards: list[Card]) -> list[Card]:
    """
    Sort cards for study with weighted ordering:
    - Overdue cards (due_date in the past) come first, most overdue first
    - New/unseen cards next
    - Cards due in the future last
    - Within each group, harder cards come first
    - Add small random jitter so it doesn't feel robotic
    """
    import random
    now = datetime.now(timezone.utc)

    def score(card: Card) -> float:
        difficulty = card.times_hard / (card.times_seen + 0.001) if card.times_seen > 0 else 0.5

        if card.times_seen == 0:
            # New card — high priority but below overdue
            base = 100.0
        elif card.due_date is None:
            # Seen but no due date set — treat as due now
            base = 90.0
        else:
            due = card.due_date
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            days_overdue = (now - due).total_seconds() / 86400
            if days_overdue >= 0:
                # Overdue: more overdue = higher priority
                base = 150.0 + days_overdue
            else:
                # Not yet due: negative value, further away = lower priority
                base = days_overdue  # negative

        jitter = random.uniform(0, 0.5)
        return base + difficulty + jitter

    return sorted(cards, key=lambda c: -score(c))
