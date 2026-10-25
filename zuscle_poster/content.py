"""Pick a topic and have Claude write the carousel copy + caption."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = os.environ.get("ZUSCLE_MODEL", "claude-sonnet-5-5")

SCHEMA_HINT = """Return ONLY valid JSON:
{
  "cover_title": "max 8 words, scroll-stopping hook",
  "cover_subtitle": "max 10 words",
  "slides": [{"heading": "max 5 words", "body": "max 25 words"}],
  "caption": "Instagram caption, 60-120 words, hook in first line, ends with a CTA to try Zuscle",
  "hashtags": ["#tag", "... 8 to 12 relevant tags"]
}
Provide exactly 4 items in "slides"."""


def load_json(name):
    return json.loads((ROOT / name).read_text())


def pick_topic(history):
    topics = load_json("topics.json")
    done = {h["topic"] for h in history}
    remaining = [t for t in topics if t["topic"] not in done]
    if not remaining:  # full cycle finished: start over
        remaining = topics
    return remaining[0]


def fallback_content(topic):
    """Used when no API key is set, so the pipeline can be tested offline."""
    return {
        "cover_title": topic["topic"][:60],
        "cover_subtitle": "Train smarter with Zuscle",
        "slides": [
            {"heading": f"Tip {i}", "body": "Placeholder tip. Set ANTHROPIC_API_KEY for real copy."}
            for i in range(1, 5)
        ],
        "caption": f"{topic['topic']}\n\nTrain smarter with your AI gym coach, Zuscle.",
        "hashtags": [],
    }


def generate(topic, brand):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set - using placeholder content")
        return fallback_content(topic)
    import anthropic

    client = anthropic.Anthropic()
    prompt = (
        f"You write Instagram carousel posts for {brand['name']}, an AI gym coach app.\n"
        f"Brand voice: {brand['voice']}\n"
        f"Content pillar: {topic['pillar']}\nTopic: {topic['topic']}\n\n"
        "Give accurate, safe, evidence-based fitness advice. No medical claims, no guaranteed "
        "results, no shaming. Mention the app naturally only in the final CTA.\n\n" + SCHEMA_HINT
    )
    msg = client.messages.create(
        model=MODEL, max_tokens=1500, messages=[{"role": "user", "content": prompt}]
    )
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    data = json.loads(text)
    assert len(data["slides"]) >= 1, "model returned no slides"
    return data


def full_caption(content, brand):
    tags = list(dict.fromkeys(content.get("hashtags", []) + brand["always_hashtags"]))[:30]
    return f"{content['caption'].strip()}\n\n{' '.join(tags)}"
