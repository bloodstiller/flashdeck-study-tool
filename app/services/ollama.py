"""
Ollama local LLM service.

Calls a locally running Ollama instance (http://localhost:11434 by default,
or OLLAMA_HOST env var) to generate resources using the same prompt as the
Claude integration — no API key required.

Recommended models (pull one before use):
  ollama pull llama3
  ollama pull mistral
  ollama pull phi3
"""

import os
import httpx
from parsers.markdown import parse_resources

OLLAMA_HOST  = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

RESOURCE_PROMPT = """\
You are a study resource curator for security certification exam prep.

Analyse these flashcard Q&A pairs, identify the key topics, and generate a curated
resources file in EXACTLY this markdown format:

## topic_name
- [Resource Title](https://real-url.com) - One-line description

Rules:
- Lowercase underscore-separated topic names (e.g. pass_the_hash, active_directory)
- 2-4 resources per topic
- REAL URLs only — PortSwigger, HackTricks, OWASP, NIST, GitHub, official docs
- No placeholder or invented URLs
- Return ONLY the markdown, no preamble or explanation

FLASHCARDS:
{cards}"""


class OllamaError(Exception):
    pass


async def is_available() -> tuple[bool, str]:
    """Check whether Ollama is running and the configured model is available."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            if resp.status_code != 200:
                return False, "Ollama is not responding"
            models = [m["name"].split(":")[0] for m in resp.json().get("models", [])]
            if OLLAMA_MODEL not in models:
                available = ", ".join(models) if models else "none"
                return False, f"Model '{OLLAMA_MODEL}' not found. Available: {available}. Run: ollama pull {OLLAMA_MODEL}"
            return True, f"Ready ({OLLAMA_MODEL})"
    except httpx.ConnectError:
        return False, f"Cannot connect to Ollama at {OLLAMA_HOST}"
    except Exception as e:
        return False, str(e)


async def generate_resources(cards: list) -> dict[str, list[dict]]:
    """
    Generate resources from card content using the local Ollama model.
    Returns parsed resource dict matching the same format as the Claude service.
    """
    ok, msg = await is_available()
    if not ok:
        raise OllamaError(msg)

    card_text = "\n\n".join(f"Q: {c.question}\nA: {c.answer}" for c in cards[:80])
    prompt    = RESOURCE_PROMPT.format(cards=card_text)

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model":  OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # low temp = more consistent formatting
                    "num_predict": 1500,
                },
            },
        )

    if resp.status_code != 200:
        raise OllamaError(f"Ollama returned HTTP {resp.status_code}: {resp.text[:200]}")

    text   = resp.json().get("response", "")
    parsed = parse_resources(text)

    if not parsed:
        raise OllamaError(
            "Model returned no parseable resources. "
            "Try a larger model: ollama pull llama3 or ollama pull mistral"
        )

    return parsed
