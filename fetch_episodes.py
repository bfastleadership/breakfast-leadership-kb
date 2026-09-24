#!/usr/bin/env python3
"""Fetch all episodes from the Breakfast Leadership Show via the Simplecast API and save as episodes.json.

The public Simplecast RSS feed is capped (~600 most-recent episodes). The Simplecast API returns the
full catalog (1,000+ episodes) with structured fields and clean per-episode page URLs. If a
SIMPLECAST_API_TOKEN environment variable is present it is sent as a Bearer token; otherwise the
public (unauthenticated) endpoint is used.
"""

import json
import os
import re
import time
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

# Show identifier (Simplecast podcast id for the Breakfast Leadership Show).
PODCAST_ID = "b517f462-4d31-4d34-8280-ea886d3d355e"
API_BASE = f"https://api.simplecast.com/podcasts/{PODCAST_ID}/episodes"
# Public per-episode page, built from each episode's slug.
SITE_BASE = "https://bfastleadership.simplecast.com/episodes"
PAGE_LIMIT = 100

# Patterns to extract guest names from titles (Simplecast has no dedicated guest field).
# Priority order: "with Name" / "featuring Name" first, then "Name |" prefix last.
GUEST_PATTERNS = [
    r"\|\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s*$",
    r"\bwith\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})(?:\s*[,\|\(]|$)",
    r"\bfeaturing\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})(?:\s*[,\|\(]|$)",
    r"\bft\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})(?:\s*[,\|\(]|$)",
    r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s+on\s+",
]

EPISODE_NUM_PATTERNS = [
    r"[Ee]pisode\s*#?\s*(\d+)",
    r"[Ee][Pp]\.?\s*#?\s*(\d+)",
    r"#(\d{3,4})\b",
]


def extract_guest(title: str):
    for pattern in GUEST_PATTERNS:
        m = re.search(pattern, title)
        if m:
            return m.group(1).strip()
    return None


def extract_episode_number(title: str, api_number):
    if api_number:
        return str(api_number)
    for pattern in EPISODE_NUM_PATTERNS:
        m = re.search(pattern, title)
        if m:
            return m.group(1)
    return None


def fetch_page(offset: int) -> dict:
    """Fetch one page of episodes from the Simplecast API."""
    url = f"{API_BASE}?limit={PAGE_LIMIT}&offset={offset}&sort=latest&status=published"
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (podcast-fetcher/1.0)",
        "Accept": "application/json",
    })
    token = os.environ.get("SIMPLECAST_API_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def to_pub_date(published_at):
    if not published_at:
        return ""
    try:
        return datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
    except ValueError:
        return published_at[:10]


def fetch_all_episodes() -> list[dict]:
    episodes = []
    offset = 0
    total = None
    while True:
        print(f"Fetching offset {offset} (limit {PAGE_LIMIT})...")
        try:
            data = fetch_page(offset)
        except URLError as e:
            print(f"Error fetching offset {offset}: {e}")
            break

        if total is None:
            total = data.get("count")
            print(f"  Catalog reports {total} episodes.")

        page = data.get("collection", [])
        if not page:
            break

        for ep in page:
            if not isinstance(ep, dict):
                continue
            if ep.get("status") != "published" or ep.get("is_hidden"):
                continue
            title = (ep.get("title") or "").strip()
            slug = (ep.get("slug") or "").strip()
            episode_url = f"{SITE_BASE}/{slug}" if slug else (ep.get("enclosure_url") or "")
            if not title or not episode_url:
                continue

            description = (ep.get("description") or "").strip()
            description = re.sub(r"<[^>]+>", " ", description)
            description = re.sub(r"\s+", " ", description).strip()

            episodes.append({
                "title": title,
                "pub_date": to_pub_date(ep.get("published_at")),
                "episode_number": extract_episode_number(title, ep.get("number")),
                "guest": extract_guest(title),
                "description": description,
                "episode_url": episode_url,
            })

        print(f"  Got {len(page)} episodes (total so far: {len(episodes)})")
        offset += PAGE_LIMIT
        if total is not None and offset >= total:
            break
        time.sleep(0.3)  # be polite to the API between pages

    return episodes


if __name__ == "__main__":
    episodes = fetch_all_episodes()
    # Deduplicate by episode_url
    seen = set()
    unique = []
    for ep in episodes:
        key = ep["episode_url"] or ep["title"]
        if key not in seen:
            seen.add(key)
            unique.append(ep)

    print(f"\nTotal unique episodes: {len(unique)}")
    with open("episodes.json", "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    print("Saved to episodes.json")
