"""Zuscle auto-poster: pick topic -> write copy -> render slides -> publish.

Usage:
  python run.py            # dry run: generates content + images in posts/<date>/, no publishing
  python run.py --publish  # also publishes to Instagram (needs IG_USER_ID, IG_ACCESS_TOKEN)

In CI, set IMAGE_BASE_URL to the public URL where posts/ is served, e.g.
  https://raw.githubusercontent.com/<owner>/<repo>/<commit-sha>
Images must be publicly reachable because the Graph API fetches them itself.
"""
import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

from zuscle_poster import content as C
from zuscle_poster import render

ROOT = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--stage", choices=["prepare", "publish"], default=None,
                    help="prepare: generate+render only; publish: post an already prepared folder")
    ap.add_argument("--dir", help="post folder for --stage publish")
    ap.add_argument("--video", action="store_true", help="also render a Reel (reel.mp4)")
    ap.add_argument("--content", help="JSON file with hand-written content (skips the Claude call)")
    args = ap.parse_args()

    history_file = ROOT / "posts" / "history.json"
    history = json.loads(history_file.read_text())
    brand = C.load_json("brand.json")

    if args.stage == "publish":
        post_dir = Path(args.dir)
    else:
        topic = C.pick_topic(history)
        print(f"Topic: {topic['topic']}")
        data = json.loads(Path(args.content).read_text()) if args.content else C.generate(topic, brand)
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d-%H%M")
        post_dir = ROOT / "posts" / stamp
        paths = render.render_all(data, brand, post_dir)
        if args.video:
            from zuscle_poster import video
            print(f"Reel: {video.render_video(data, brand, post_dir / 'reel.mp4')}")
        caption = C.full_caption(data, brand)
        meta = {"topic": topic["topic"], "pillar": topic["pillar"], "caption": caption,
                "images": [p.name for p in paths], "published": False}
        (post_dir / "post.json").write_text(json.dumps(meta, indent=2))
        print(f"Prepared {len(paths)} slides in {post_dir}")
        if args.stage == "prepare" or not args.publish:
            print("\n--- CAPTION ---\n" + caption)
            print(f"POST_DIR={post_dir}")
            return

    meta = json.loads((post_dir / "post.json").read_text())
    base_url = os.environ.get("IMAGE_BASE_URL", "").rstrip("/")
    if not base_url:
        sys.exit("IMAGE_BASE_URL is required to publish")
    from zuscle_poster import instagram
    rel = post_dir.relative_to(ROOT).as_posix()
    urls = [f"{base_url}/{rel}/{n}" for n in meta["images"]]
    media_id = instagram.publish_carousel(urls, meta["caption"])
    print(f"Published media id {media_id}")

    meta["published"] = True
    meta["media_id"] = media_id
    (post_dir / "post.json").write_text(json.dumps(meta, indent=2))
    history.append({"topic": meta["topic"], "dir": rel, "media_id": media_id,
                    "at": dt.datetime.now(dt.timezone.utc).isoformat()})
    history_file.write_text(json.dumps(history, indent=2))


if __name__ == "__main__":
    main()
