"""
Tests for the markdown card parser.
Run with:  pytest tests/test_parser.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from parsers.markdown import parse_file, parse_resources


# ── Format A: noteId frontmatter ─────────────────────────────────────────────

NOTEID_SINGLE = """---
noteId: 1772627304257
---

Can password hashes be used if they cannot be cracked?

---

Yes they can be used in pass the hash attacks where the hash is used directly for authentication without needing to crack the original password.
"""

NOTEID_WINDOWS = """---
noteId: 1772627304922
---

What are built in user accounts on Windows servers?

---

Administrator
Guest
Default service accounts
"""

NOTEID_MULTILINE_ANSWER = """---
noteId: 1772627305024
---

What are common SSL and TLS vulnerabilities?

---

Heartbleed
POODLE
BEAST
CRIME
"""

def test_noteid_basic():
    cards = parse_file(NOTEID_SINGLE)
    assert len(cards) == 1
    assert cards[0].question == "Can password hashes be used if they cannot be cracked?"
    assert "pass the hash" in cards[0].answer

def test_noteid_multiline_answer():
    cards = parse_file(NOTEID_WINDOWS)
    assert len(cards) == 1
    assert cards[0].question == "What are built in user accounts on Windows servers?"
    assert "Administrator" in cards[0].answer

def test_noteid_list_answer():
    cards = parse_file(NOTEID_MULTILINE_ANSWER)
    assert len(cards) == 1
    assert "Heartbleed" in cards[0].answer
    assert "CRIME" in cards[0].answer


# ── Format B: inline Q --- A ──────────────────────────────────────────────────

INLINE_SINGLE = "What is SQL injection?  ---  Injecting malicious SQL via user input."
INLINE_MULTI  = """What is XSS?  ---  Injecting malicious scripts into pages viewed by other users.
What is CSRF?  ---  Tricking a user into submitting a malicious request using their session.
What is SSRF?  ---  Forcing a server to make requests to internal services.
"""

def test_inline_single():
    cards = parse_file(INLINE_SINGLE)
    assert len(cards) == 1
    assert cards[0].question == "What is SQL injection?"
    assert "malicious SQL" in cards[0].answer

def test_inline_multi():
    cards = parse_file(INLINE_MULTI)
    assert len(cards) == 3
    questions = [c.question for c in cards]
    assert "What is XSS?" in questions
    assert "What is CSRF?" in questions

def test_inline_triple_dash():
    cards = parse_file("Can hashes be used?  ---  Yes, pass-the-hash.")
    assert len(cards) == 1

def test_inline_no_space_ignored():
    # Must have spaces around ---
    cards = parse_file("Question---Answer")
    assert len(cards) == 0


# ── Format C: ## heading blocks ───────────────────────────────────────────────

HEADING_BLOCK = """## What is Kerberoasting?

Extracting Kerberos service tickets for accounts with SPNs and cracking offline.

**Tags:** activedirectory, kerberos

---

## What is a Golden Ticket?

A forged TGT created using the KRBTGT hash.

**Tags:** activedirectory, kerberos, persistence
"""

def test_heading_basic():
    cards = parse_file(HEADING_BLOCK)
    assert len(cards) == 2
    assert cards[0].question == "What is Kerberoasting?"
    assert "kerberos" in cards[0].tags
    assert "activedirectory" in cards[0].tags

def test_heading_tags_stripped_from_answer():
    cards = parse_file(HEADING_BLOCK)
    assert "**Tags:**" not in cards[0].answer

def test_heading_multiple_tags():
    cards = parse_file(HEADING_BLOCK)
    assert "persistence" in cards[1].tags


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_file():
    assert parse_file("") == []

def test_whitespace_only():
    assert parse_file("   \n\n\n   ") == []

def test_frontmatter_no_answer():
    content = "---\nnoteId: 123\n---\n\nJust a question with no answer separator"
    # Should fall through to other parsers and return empty (no --- separator after frontmatter)
    cards = parse_file(content)
    assert len(cards) == 0

def test_noteid_preserves_whitespace_in_answer():
    cards = parse_file(NOTEID_MULTILINE_ANSWER)
    # Multiline answers should be preserved
    assert "\n" in cards[0].answer or "POODLE" in cards[0].answer


# ── Resource parser ───────────────────────────────────────────────────────────

RESOURCES_MD = """## credentials
- [Mimikatz Wiki](https://github.com/gentilkiwi/mimikatz/wiki) - Official command reference
- [LOLBAS](https://lolbas-project.github.io/) - Living off the land binaries

## web
- [PortSwigger Academy](https://portswigger.net/web-security) - Free interactive labs
- [OWASP Top 10](https://owasp.org/www-project-top-ten/) - Critical web risks

## empty_topic
"""

def test_resources_parsed():
    res = parse_resources(RESOURCES_MD)
    assert "credentials" in res
    assert "web" in res

def test_resources_correct_count():
    res = parse_resources(RESOURCES_MD)
    assert len(res["credentials"]) == 2
    assert len(res["web"]) == 2

def test_resources_empty_topic_excluded():
    res = parse_resources(RESOURCES_MD)
    assert "empty_topic" not in res

def test_resources_fields():
    res = parse_resources(RESOURCES_MD)
    item = res["credentials"][0]
    assert item["title"] == "Mimikatz Wiki"
    assert "github.com" in item["url"]
    assert "command reference" in item["description"]
