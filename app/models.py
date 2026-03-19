from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


# Many-to-many: cards <-> tags
card_tags = Table(
    "card_tags",
    Base.metadata,
    Column("card_id", Integer, ForeignKey("cards.id", ondelete="CASCADE")),
    Column("tag_id",  Integer, ForeignKey("tags.id",  ondelete="CASCADE")),
)


class Card(Base):
    __tablename__ = "cards"

    id          = Column(Integer, primary_key=True, index=True)
    question    = Column(Text, nullable=False)
    answer      = Column(Text, nullable=False)
    source_file = Column(String(512), nullable=True)   # original filename
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    # Difficulty tracking (aggregated across all sessions)
    times_seen    = Column(Integer, default=0)
    times_correct = Column(Integer, default=0)
    times_hard    = Column(Integer, default=0)

    pinned        = Column(Boolean, default=False)
    notes         = Column(Text, nullable=True)

    # Spaced repetition (simplified SM-2)
    due_date      = Column(DateTime(timezone=True), nullable=True)
    interval_days = Column(Integer, default=1)
    ease_factor   = Column(Float, default=2.5)
    last_reviewed = Column(DateTime(timezone=True), nullable=True)

    tags    = relationship("Tag", secondary=card_tags, back_populates="cards")
    results = relationship("CardResult", back_populates="card", cascade="all, delete-orphan")

    @property
    def difficulty_score(self) -> float:
        """0.0 = easy, 1.0 = very hard. Used to prioritise review order."""
        if self.times_seen == 0:
            return 0.5  # unseen cards are neutral
        return self.times_hard / self.times_seen


class Tag(Base):
    __tablename__ = "tags"

    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    cards = relationship("Card", secondary=card_tags, back_populates="tags")


class Resource(Base):
    __tablename__ = "resources"

    id          = Column(Integer, primary_key=True, index=True)
    topic       = Column(String(100), nullable=False, index=True)
    title       = Column(String(255), nullable=False)
    url         = Column(String(2048), nullable=False)
    description = Column(Text, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


class StudySession(Base):
    __tablename__ = "study_sessions"

    id         = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at   = Column(DateTime(timezone=True), nullable=True)
    mode       = Column(String(50), default="all")  # all | hard | tag:<name>

    results = relationship("CardResult", back_populates="session", cascade="all, delete-orphan")

    @property
    def total(self):
        return len(self.results)

    @property
    def got(self):
        return sum(1 for r in self.results if r.result == "got")

    @property
    def hard(self):
        return sum(1 for r in self.results if r.result == "hard")

    @property
    def skipped(self):
        return sum(1 for r in self.results if r.result == "skip")


class CardResult(Base):
    __tablename__ = "card_results"

    id         = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("study_sessions.id", ondelete="CASCADE"))
    card_id    = Column(Integer, ForeignKey("cards.id",           ondelete="CASCADE"))
    result     = Column(String(10), nullable=False)   # got | hard | skip
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("StudySession", back_populates="results")
    card    = relationship("Card",         back_populates="results")
