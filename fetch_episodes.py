#!/usr/bin/env python3
"""Fetch all episodes from the Breakfast Leadership Show RSS feed and save as episodes.json."""

import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

FEED_URL = "https://feed.podbean.com/bfastleadership/feed.xml"

NAMESPACES = {
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "atom": "http://www.w3.org/2005/Atom",
}

# Patterns to extract guest names from titles
# Priority order: "with Name" / "featuring Name" first, then "Name |" prefix last
GUEST_PATTERNS = [
    # "...with John Smith" at end or before separator
    r"\|\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s*$",
    r"\bwith\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})(?:\s*[,\|\(]|$)",
    r"\bfeaturing\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})(?:\s*[,\|\(]|$)",
    r"\bft\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})(?:\s*[,\|\(]|$)",
    # "Name on/:" prefix — only match if followed by a topic word (not a single common word)
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


def extract_episode_number(title: str, itunes_episode):
    if itunes_episode:
        return itunes_episode
    for pattern in EPISODE_NUM_PATTERNS:
        m = re.search(pattern, title)
        if m:
            return m.group(1)
    return None


def parse_feed_page(url: str):
    """Fetch one page of the feed; return (episodes, next_url)."""
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (podcast-fetcher/1.0)"})
    with urlopen(req, timeout=30) as resp:
        data = resp.read()

    root = ET.fromstring(data)
    channel = root.find("channel")
    if channel is None:
        return [], None

    # Look for atom:link rel="next"
    next_url = None
    for link in channel.findall("{http://www.w3.org/2005/Atom}link"):
        if link.get("rel") == "next":
            next_url = link.get("href")
            break

    episodes = []
    for item in channel.findall("item"):
        title_el = item.find("title")
        title = title_el.text.strip() if title_el is not None and title_el.text else ""

        pub_date_el = item.find("pubDate")
        pub_date_raw = pub_date_el.text.strip() if pub_date_el is not None and pub_date_el.text else ""
        try:
            pub_date = datetime.strptime(pub_date_raw, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d")
        except ValueError:
            pub_date = pub_date_raw

        link_el = item.find("link")
        episode_url = link_el.text.strip() if link_el is not None and link_el.text else ""

        enclosure = item.find("enclosure")
        if not episode_url and enclosure is not None:
            episode_url = enclosure.get("url", "")

        desc_el = item.find("description")
        description = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
        # Also check itunes:summary
        if not description:
            summary_el = item.find("itunes:summary", NAMESPACES)
            if summary_el is not None and summary_el.text:
                description = summary_el.text.strip()
        # Strip HTML tags from description
        description = re.sub(r"<[^>]+>", " ", description)
        description = re.sub(r"\s+", " ", description).strip()

        itunes_ep_el = item.find("itunes:episode", NAMESPACES)
        itunes_episode = itunes_ep_el.text.strip() if itunes_ep_el is not None and itunes_ep_el.text else None

        episode_number = extract_episode_number(title, itunes_episode)
        guest = extract_guest(title)

        episodes.append({
            "title": title,
            "pub_date": pub_date,
            "episode_number": episode_number,
            "guest": guest,
            "description": description,
            "episode_url": episode_url,
        })

    return episodes, next_url


def fetch_all_episodes() -> list[dict]:
    all_episodes = []
    url = FEED_URL
    page = 1

    while url:
        print(f"Fetching page {page}: {url}")
        try:
            episodes, next_url = parse_feed_page(url)
        except URLError as e:
            print(f"Error fetching {url}: {e}")
            break

        if not episodes:
            print("No episodes found on this page, stopping.")
            break

        all_episodes.extend(episodes)
        print(f"  Got {len(episodes)} episodes (total so far: {len(all_episodes)})")
        url = next_url
        page += 1

    return all_episodes


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
