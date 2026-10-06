#!/usr/bin/env python3
"""Fetch all episodes from the Breakfast Leadership Show via the Simplecast API and save as episodes.json.

Data (titles, descriptions, dates, the full 1,000+ catalog) comes from the Simplecast API, because its
public RSS feed is capped (~600) and Apple's API only exposes the most recent ~200 episodes.

Clickable links (link_url) point to Apple Podcasts, because the Simplecast episode pages do not load.
Each Simplecast episode is matched to its Apple episode page by GUID; episodes Apple does not expose
(older than ~mid-2025) fall back to the show's main Apple Podcasts page.

episode_url stays a unique Simplecast slug URL and is used only as the internal key (de-duplication and
the "Ask AI" result matching). link_url is what the page actually links to.

If a SIMPLECAST_API_TOKEN environment variable is present it is sent as a Bearer token; otherwise the
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
# Unique internal key per episode, built from each episode's slug (never shown; Simplecast pages do not load).
SITE_BASE = "https://bfastleadership.simplecast.com/episodes"
PAGE_LIMIT = 100

# Apple Podcasts, used for the customer-facing links.
APPLE_PODCAST_ID = "1207338410"
APPLE_LOOKUP_URL = (
    f"https://itunes.apple.com/lookup?id={APPLE_PODCAST_ID}"
    "&country=ca&media=podcast&entity=podcastEpisode&limit=200"
)
APPLE_SHOW_URL = f"https://podcasts.apple.com/ca/podcast/breakfast-leadership-show/id{APPLE_PODCAST_ID}"

# Patterns to extract guest names from titles (Simplecast has no dedicated guest field).
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


def fetch_apple_links() -> dict:
    """Map Simplecast/Apple episode GUID -> Apple Podcasts episode page URL (recent ~200 episodes)."""
    try:
        req = Request(APPLE_LOOKUP_URL, headers={"User-Agent": "Mozilla/5.0 (podcast-fetcher/1.0)"})
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        links = {}
        for r in data.get("results", []):
            if r.get("wrapperType") == "podcastEpisode" and r.get("episodeGuid") and r.get("trackViewUrl"):
                links[r["episodeGuid"]] = r["trackViewUrl"]
        print(f"  Apple: mapped {len(links)} episode page links.")
        return links
    except Exception as e:
        print(f"  Apple lookup failed ({e}); all links will use the show page.")
        return {}


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
                "guid": ep.get("guid"),  # temporary, used to match Apple links; removed before saving
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

    # Attach customer-facing Apple link per episode (exact page where Apple has it, else the show page).
    apple_links = fetch_apple_links()
    matched = 0
    for ep in unique:
        guid = ep.pop("guid", None)
        link = apple_links.get(guid)
        if link:
            matched += 1
        ep["link_url"] = link or APPLE_SHOW_URL

    print(f"\nTotal unique episodes: {len(unique)} (exact Apple links: {matched}, show-page fallback: {len(unique) - matched})")
    with open("episodes.json", "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    print("Saved to episodes.json")
