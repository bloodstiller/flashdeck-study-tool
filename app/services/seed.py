"""
Seed service — loads the bundled app/resources_seed.md into the database
on first run (when the resources table is empty).

The seed file lives inside app/ so it is always copied into the Docker
image by the existing COPY app/ ./app/ directive in the Dockerfile.
"""

from pathlib import Path
from sqlalchemy.orm import Session
from app.models import Resource
from parsers.markdown import parse_resources

# app/services/seed.py  →  parent = app/services/  →  parent.parent = app/
SEED_FILE = Path(__file__).parent.parent / "resources_seed.md"


def seed_resources(db: Session) -> int:
    """
    Load resources_seed.md into the DB if no resources exist yet.
    Returns the number of resources inserted.
    """
    if db.query(Resource).count() > 0:
        return 0

    if not SEED_FILE.exists():
        return 0

    return _load_seed_file(db)


def reload_seed(db: Session) -> int:
    """
    Force-reload the seed file, adding any entries not already in the DB.
    Never removes existing resources — purely additive.
    Returns number of new resources inserted.
    """
    if not SEED_FILE.exists():
        raise FileNotFoundError(f"Seed file not found at {SEED_FILE}")

    return _load_seed_file(db)


def _load_seed_file(db: Session) -> int:
    content = SEED_FILE.read_text(encoding="utf-8")
    parsed  = parse_resources(content)

    count = 0
    for topic, items in parsed.items():
        for item in items:
            exists = db.query(Resource).filter(Resource.url == item["url"]).first()
            if not exists:
                db.add(Resource(
                    topic=topic,
                    title=item["title"],
                    url=item["url"],
                    description=item.get("description", ""),
                ))
                count += 1

    db.commit()
    return count
