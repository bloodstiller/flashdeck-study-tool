"""
Markdown card parser.

Supported formats
─────────────────
A) noteId frontmatter (one card per file):

    ---
    noteId: 1772627304257
    ---

    Question text

    ---

    Answer text

B) Inline Q --- A (one card per line):

    Can hashes be used without cracking?  ---  Yes, via pass-the-hash.

C) ## Heading blocks separated by horizontal rules:

    ## What is SQL injection?

    SQL injection allows...

    **Tags:** web, sqli

    ---
"""

import re
from dataclasses import dataclass, field


@dataclass
class ParsedCard:
    question: str
    answer:   str
    tags:     list[str] = field(default_factory=list)


def parse_file(content: str) -> list[ParsedCard]:
    """Parse a single markdown file's content into a list of ParsedCards."""
    content = content.strip()

    # ── Format A: YAML frontmatter + single Q/A separated by ---
    fm_match = re.match(r'^---[\s\S]*?---\n([\s\S]*)$', content)
    if fm_match:
        body = fm_match.group(1).strip()
        parts = re.split(r'\n\s*---+\s*\n', body, maxsplit=1)
        if len(parts) == 2:
            q, a = parts[0].strip(), parts[1].strip()
            if q and a:
                return [ParsedCard(question=q, answer=a)]

    # ── Format B: inline  Q  ---  A  per line
    inline_cards = []
    for line in content.splitlines():
        m = re.match(r'^(.+?)\s+---+\s+(.+)$', line)
        if m:
            q, a = m.group(1).strip(), m.group(2).strip()
            if q and a:
                inline_cards.append(ParsedCard(question=q, answer=a))
    if inline_cards:
        return inline_cards

    # ── Format C: ## heading blocks
    heading_cards = []
    sections = re.split(r'\n---+\n', content)
    for sec in sections:
        sec = sec.strip()
        if len(sec) < 8:
            continue
        h2 = re.search(r'^##\s+(.+)$', sec, re.MULTILINE)
        if not h2:
            continue
        question = h2.group(1).strip()
        rest = re.sub(r'^##\s+.+$', '', sec, count=1, flags=re.MULTILINE).strip()
        tags: list[str] = []
        tag_match = re.search(r'\*\*Tags?:\*\*\s*(.+)$', rest, re.IGNORECASE | re.MULTILINE)
        if tag_match:
            tags = [t.strip().lower() for t in tag_match.group(1).split(',') if t.strip()]
            rest = re.sub(r'\*\*Tags?:\*\*\s*.+$', '', rest, flags=re.IGNORECASE | re.MULTILINE).strip()
        if question and rest:
            heading_cards.append(ParsedCard(question=question, answer=rest, tags=tags))
    return heading_cards


def parse_resources(content: str) -> dict[str, list[dict]]:
    """
    Parse a resources markdown file.

    ## topic_name
    - [Title](url) - description
    """
    result: dict[str, list[dict]] = {}
    topic = None
    for line in content.splitlines():
        h2 = re.match(r'^##\s+(.+)$', line)
        if h2:
            topic = h2.group(1).strip().lower()
            result[topic] = []
            continue
        if topic:
            m = re.match(r'^-\s*\[(.+?)\]\((.+?)\)(?:\s*[-–]\s*(.+))?', line)
            if m:
                result[topic].append({
                    "title":       m.group(1),
                    "url":         m.group(2),
                    "description": m.group(3).strip() if m.group(3) else "",
                })
    # drop empty topics
    return {k: v for k, v in result.items() if v}
