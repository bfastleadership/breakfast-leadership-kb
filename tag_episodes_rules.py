#!/usr/bin/env python3
"""
Rule-based tagger fallback: assigns subject tags from keyword matching.
Run this if ANTHROPIC_API_KEY is not yet available, or as a pre-pass
before the API tagger overwrites with better results.
"""

import json
import re

RULES: list[tuple[str, list[str]]] = [
    ("burnout|burnt.out|burn out|exhaustion|overwork", ["Burnout Prevention", "Mental Health"]),
    ("ai |artificial intelligence|machine learning|gpt|chatgpt|llm|generative ai", ["AI Strategy", "Technology"]),
    ("cybersecurity|cyber security|hack|breach|zero trust|phishing|malware|ransomware", ["Cybersecurity", "Technology"]),
    ("real estate|property|mortgage|housing|landlord|reit|commercial property", ["Real Estate", "Finance"]),
    ("mental health|anxiety|depression|stress|therapy|well.?being|mindfulness|meditation", ["Mental Health", "Health & Wellness"]),
    ("entrepreneur|startup|founder|venture|bootstrap|small business", ["Entrepreneurship"]),
    ("leadership|leader|executive|ceo|c.suite|management", ["Leadership"]),
    ("culture|workplace|employee|team|diversity|inclusion|belonging", ["Workplace Culture", "Team Building"]),
    ("decision.making|strategic|strategy|vision|planning", ["Executive Decision-Making", "Strategy"]),
    ("sales|revenue|pipeline|prospect|crm|closing|quota", ["Sales"]),
    ("finance|financ|invest|capital|budget|cash flow|profit|loss|accounting|cfo", ["Finance"]),
    ("productivity|efficiency|time management|workflow|automation|systems", ["Productivity"]),
    ("resilience|adversity|overcome|grit|persevere|bounce back|tough", ["Resilience", "Mindset"]),
    ("coach|mentor|develop|grow|career|talent|performance review", ["Coaching", "Career Growth"]),
    ("communication|public speaking|storytelling|presentation|podcast", ["Communication", "Public Speaking"]),
    ("marketing|brand|content|seo|social media|advertising|campaign", ["Marketing", "Branding"]),
    ("customer|client|service|experience|satisfaction|retention", ["Customer Experience"]),
    ("innovation|disrupt|creative|idea|invention|R&D", ["Innovation"]),
    ("remote|hybrid|wfh|work from home|distributed team", ["Remote Work", "Workplace Culture"]),
    ("health|fitness|nutrition|sleep|exercise|wellness", ["Health & Wellness"]),
    ("mindset|mindfulness|attitude|belief|growth mindset|self.?improve", ["Mindset", "Personal Development"]),
    ("negotiation|negotiat|deal|contract|persuasion", ["Negotiation", "Communication"]),
    ("network|relationship|connection|community|collaboration", ["Networking"]),
    ("technology|tech|software|digital|data|cloud|saas|platform", ["Technology"]),
    ("education|learn|training|course|skill|knowledge", ["Education", "Personal Development"]),
    ("operations|process|supply chain|logistics|ops|system", ["Operations"]),
]

DEFAULT_TAGS = ["Leadership", "Personal Development"]


def tag_episode(title: str, description: str) -> list[str]:
    text = (title + " " + description).lower()
    found: set[str] = set()
    for pattern, tags in RULES:
        if re.search(pattern, text):
            found.update(tags)
        if len(found) >= 5:
            break
    result = list(found)[:5]
    if not result:
        result = DEFAULT_TAGS.copy()
    return result


def main():
    with open("episodes.json", encoding="utf-8") as f:
        episodes = json.load(f)

    for ep in episodes:
        ep["tags"] = tag_episode(ep.get("title", ""), ep.get("description", ""))

    with open("episodes_tagged.json", "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)

    print(f"Tagged {len(episodes)} episodes (rule-based). Saved to episodes_tagged.json")
    print("\nSample tags:")
    for ep in episodes[:5]:
        print(f"  {ep['title'][:50]} → {ep['tags']}")


if __name__ == "__main__":
    main()
