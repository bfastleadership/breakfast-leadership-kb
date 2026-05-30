#!/usr/bin/env python3
"""Tag each episode with 3-5 subject tags using the Anthropic API."""

import json
import os
import time
import anthropic

TAXONOMY = [
    "Leadership", "Burnout Prevention", "AI Strategy", "Workplace Culture",
    "Entrepreneurship", "Executive Decision-Making", "Mental Health", "Real Estate",
    "Cybersecurity", "Sales", "Finance", "Productivity", "Resilience", "Team Building",
    "Communication", "Marketing", "Customer Experience", "Innovation", "Career Growth",
    "Diversity & Inclusion", "Remote Work", "Personal Development", "Health & Wellness",
    "Strategy", "Technology", "Education", "Mindset", "Coaching", "Operations",
    "Negotiation", "Public Speaking", "Networking", "Social Media", "Branding",
]

SYSTEM_PROMPT = f"""You are a podcast content classifier. Given an episode title and description,
assign exactly 3 to 5 subject tags from the following taxonomy. Return ONLY a JSON array of tag strings.
Choose the most specific and relevant tags. Do not invent new tags outside the taxonomy.

Taxonomy: {json.dumps(TAXONOMY)}"""


def get_tags(client: anthropic.Anthropic, title: str, description: str) -> list[str]:
    user_msg = f"Title: {title}\n\nDescription: {description[:1500]}"
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = response.content[0].text.strip()
    # Parse JSON array
    tags = json.loads(text)
    # Validate all tags are in taxonomy
    valid = [t for t in tags if t in TAXONOMY]
    return valid[:5] if valid else tags[:5]


def main():
    with open("episodes.json", encoding="utf-8") as f:
        episodes = json.load(f)

    # Load existing tagged file if present (for resuming)
    tagged_path = "episodes_tagged.json"
    tagged_map: dict[str, list[str]] = {}
    if os.path.exists(tagged_path):
        with open(tagged_path, encoding="utf-8") as f:
            existing = json.load(f)
        for ep in existing:
            if "tags" in ep:
                tagged_map[ep.get("episode_url") or ep.get("title", "")] = ep["tags"]
        print(f"Resuming: {len(tagged_map)} episodes already tagged.")

    client = anthropic.Anthropic()

    tagged_episodes = []
    for i, ep in enumerate(episodes):
        key = ep.get("episode_url") or ep.get("title", "")
        if key in tagged_map:
            ep["tags"] = tagged_map[key]
            tagged_episodes.append(ep)
            continue

        try:
            tags = get_tags(client, ep["title"], ep.get("description", ""))
            ep["tags"] = tags
            print(f"[{i+1}/{len(episodes)}] {ep['title'][:60]} → {tags}")
        except Exception as e:
            print(f"[{i+1}/{len(episodes)}] ERROR for '{ep['title'][:40]}': {e}")
            ep["tags"] = []

        tagged_episodes.append(ep)

        # Save checkpoint every 50 episodes
        if (i + 1) % 50 == 0:
            with open(tagged_path, "w", encoding="utf-8") as f:
                json.dump(tagged_episodes, f, indent=2, ensure_ascii=False)
            print(f"  Checkpoint saved ({i+1} episodes processed)")

        # Rate limiting: ~3 req/sec to stay within Haiku limits
        time.sleep(0.35)

    with open(tagged_path, "w", encoding="utf-8") as f:
        json.dump(tagged_episodes, f, indent=2, ensure_ascii=False)
    print(f"\nDone. Saved {len(tagged_episodes)} tagged episodes to {tagged_path}")


if __name__ == "__main__":
    main()
