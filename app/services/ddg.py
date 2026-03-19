"""
DuckDuckGo resource search — no API key required.

Uses two DDG endpoints:
  1. Instant Answer API  (api.duckduckgo.com) — structured results, zero-click info
  2. HTML search scrape  (html.duckduckgo.com) — organic results as fallback

Both are intentionally rate-limit friendly: we fire one request per topic
and parse whatever comes back, rather than hammering the API.
"""

import re
import asyncio
import httpx
from dataclasses import dataclass

DDG_INSTANT_URL = "https://api.duckduckgo.com/"
DDG_HTML_URL    = "https://html.duckduckgo.com/html/"

HEADERS = {
    "User-Agent": "FlashDeck/2.0 (educational flashcard app; not scraping for commercial use)",
    "Accept-Language": "en-GB,en;q=0.9",
}

# Security-specific site allowlist — prefer results from these domains
PREFERRED_DOMAINS = [
    "portswigger.net",
    "owasp.org",
    "book.hacktricks.xyz",
    "github.com",
    "nist.gov",
    "nvd.nist.gov",
    "docs.microsoft.com",
    "learn.microsoft.com",
    "gtfobins.github.io",
    "lolbas-project.github.io",
    "exploit-db.com",
    "thehacker.recipes",
    "attack.mitre.org",
]


@dataclass
class SearchResult:
    title:       str
    url:         str
    description: str


async def search_topic(topic: str, max_results: int = 4) -> list[SearchResult]:
    """
    Search DDG for a security topic and return up to max_results links.
    Combines instant-answer results with organic HTML results.
    """
    query = _build_query(topic)
    results: list[SearchResult] = []

    async with httpx.AsyncClient(headers=HEADERS, timeout=10, follow_redirects=True) as client:
        # Try instant answer API first
        try:
            instant = await _instant_search(client, query)
            results.extend(instant)
        except Exception:
            pass

        # Supplement with HTML organic results if needed
        if len(results) < max_results:
            try:
                organic = await _html_search(client, query, max_results * 3)
                for r in organic:
                    if r.url not in {x.url for x in results}:
                        results.append(r)
            except Exception:
                pass

    # Rank: preferred domains first, then others
    preferred = [r for r in results if any(d in r.url for d in PREFERRED_DOMAINS)]
    others    = [r for r in results if r not in preferred]
    ranked    = preferred + others

    return ranked[:max_results]


async def search_topics(topics: list[str], max_per_topic: int = 3) -> dict[str, list[SearchResult]]:
    """Search multiple topics concurrently with a small delay between batches."""
    results: dict[str, list[SearchResult]] = {}
    # Process in pairs to avoid hammering DDG
    for i in range(0, len(topics), 2):
        batch = topics[i:i + 2]
        tasks = [search_topic(t, max_per_topic) for t in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        for topic, res in zip(batch, batch_results):
            if isinstance(res, list):
                results[topic] = res
        if i + 2 < len(topics):
            await asyncio.sleep(0.8)  # polite delay between batches
    return results


# ── Instant Answer API ────────────────────────────────────────────────────────

async def _instant_search(client: httpx.AsyncClient, query: str) -> list[SearchResult]:
    resp = await client.get(DDG_INSTANT_URL, params={
        "q":              query,
        "format":         "json",
        "no_redirect":    "1",
        "no_html":        "1",
        "skip_disambig":  "1",
    })
    resp.raise_for_status()
    data = resp.json()
    results = []

    # RelatedTopics contains the most reliable structured links
    for item in data.get("RelatedTopics", []):
        if "Topics" in item:
            for sub in item["Topics"]:
                r = _parse_instant_item(sub)
                if r:
                    results.append(r)
        else:
            r = _parse_instant_item(item)
            if r:
                results.append(r)

    # Abstract link (Wikipedia-style)
    if data.get("AbstractURL") and data.get("AbstractText"):
        results.insert(0, SearchResult(
            title=data.get("Heading", query),
            url=data["AbstractURL"],
            description=data["AbstractText"][:150].rstrip() + "…",
        ))

    return results


def _parse_instant_item(item: dict) -> SearchResult | None:
    url  = item.get("FirstURL", "")
    text = item.get("Text", "")
    if not url or not text:
        return None
    # DDG instant results often look like "Title - Description"
    parts = text.split(" - ", 1)
    title = parts[0].strip()[:80]
    desc  = parts[1].strip()[:150] if len(parts) > 1 else text[:150]
    return SearchResult(title=title, url=url, description=desc)


# ── HTML organic search ───────────────────────────────────────────────────────

async def _html_search(client: httpx.AsyncClient, query: str, limit: int) -> list[SearchResult]:
    resp = await client.post(DDG_HTML_URL, data={"q": query})
    resp.raise_for_status()
    return _parse_html_results(resp.text, limit)


def _parse_html_results(html: str, limit: int) -> list[SearchResult]:
    """
    Parse DuckDuckGo HTML search results.
    DDG HTML page has result links in <a class="result__a"> elements.
    """
    results = []

    # Extract result blocks
    result_pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
        r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
        re.DOTALL,
    )

    for m in result_pattern.finditer(html):
        url   = _clean_ddg_url(m.group(1))
        title = _strip_tags(m.group(2))[:80]
        desc  = _strip_tags(m.group(3))[:150]
        if url and title and url.startswith("http"):
            results.append(SearchResult(title=title, url=url, description=desc))
        if len(results) >= limit:
            break

    # Fallback: simpler link extraction if the above finds nothing
    if not results:
        link_pattern = re.compile(r'href="(https?://[^"]+)"[^>]*>([^<]{10,80})</a>')
        seen = set()
        for m in link_pattern.finditer(html):
            url   = m.group(1)
            title = m.group(2).strip()
            if url not in seen and "duckduckgo" not in url:
                seen.add(url)
                results.append(SearchResult(title=title, url=url, description=""))
            if len(results) >= limit:
                break

    return results


def _clean_ddg_url(url: str) -> str:
    """DDG sometimes wraps URLs in redirect links — extract the real one."""
    m = re.search(r'uddg=([^&]+)', url)
    if m:
        from urllib.parse import unquote
        return unquote(m.group(1))
    return url


def _strip_tags(html: str) -> str:
    return re.sub(r'<[^>]+>', '', html).strip()


def _build_query(topic: str) -> str:
    """Turn a topic key like 'pass_the_hash' into a good security search query."""
    readable = topic.replace("_", " ")
    # Add "security" context if the topic isn't already clearly security-related
    security_terms = {"security", "attack", "exploit", "vulnerability", "injection",
                      "hash", "kerberos", "privilege", "escalation", "enumeration"}
    words = set(readable.lower().split())
    if not words & security_terms:
        return f"{readable} cybersecurity pentest"
    return f"{readable} site:portswigger.net OR site:owasp.org OR site:book.hacktricks.xyz OR site:github.com"
