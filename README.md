# Zuscle Instagram auto-poster

Fully automated Instagram carousels for the Zuscle AI gym coach app.

```
topics.json -> Claude writes copy -> Pillow renders 1080x1350 slides -> Instagram Graph API publishes
                                  (GitHub Actions runs it on a schedule)
```

Each post is a 6-slide carousel: hook cover, 4 tips, call-to-action. Caption and hashtags are generated too.

## Try it locally (no publishing)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...     # optional; without it you get placeholder copy
python run.py                    # writes posts/<timestamp>/slide_*.jpg + post.json, prints caption
```

## One-time setup for auto-posting

1. **Instagram**: switch the account to Business/Creator and link it to a Facebook Page. Create a Meta app,
   add the Instagram Graph API, and get a long-lived access token with `instagram_basic` and
   `instagram_content_publish`. Note your Instagram user ID. (Long-lived tokens last ~60 days; refresh
   before expiry.)
2. **Repo secrets** (Settings -> Secrets -> Actions): `ANTHROPIC_API_KEY`, `IG_USER_ID`, `IG_ACCESS_TOKEN`.
3. **The repo must be public.** Instagram downloads images from a URL, and the workflow serves them via
   `raw.githubusercontent.com`. For a private repo, change `IMAGE_BASE_URL` to S3/R2/GitHub Pages.
4. Run the workflow manually from the Actions tab (leave "publish" off for a dry run, then on).

The schedule is in `.github/workflows/post.yml` (default Mon/Wed/Fri 11:30 UTC).

## Customise

- `brand.json` - colours, handle, voice, always-on hashtags.
- `topics.json` - content calendar; topics are used in order and the list restarts when exhausted.
  `posts/history.json` tracks what has been published.
- `zuscle_poster/render.py` - slide design.
- `ZUSCLE_MODEL` env var overrides the Claude model.

Instagram limits: 100 API-published posts per 24h and 30 hashtags per post (the code caps at 30).
