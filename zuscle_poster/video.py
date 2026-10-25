"""Render a 1080x1920 Reel (mp4, silent) from the same content used for the carousel."""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from .render import font, gradient, hex_rgb, wrap, BOLD, REG

VW, VH = 1080, 1920
FPS = 30
SCENE_SECONDS = 3.2
PAD = 100
MAX_W = VW - 2 * PAD
SLIDE_PX = 50      # elements slide up this far while fading in
FADE_FRAMES = 14
# Reels UI covers the top ~200px and bottom ~340px, so keep content between them.


def scenes(content, brand):
    out = [[("big", content["cover_title"], "text"), ("sub", content["cover_subtitle"], "muted")]]
    for i, s in enumerate(content["slides"], 1):
        out.append([("num", f"{i:02d}", "accent"), ("head", s["heading"], "text"),
                    ("body", s["body"], "muted")])
    out.append([("big", "Train smarter, not harder.", "text"), ("sub", brand["cta"], "muted"),
                ("btn", "Link in bio", "accent")])
    return out


STYLE = {"big": (BOLD, 104, 1.15), "sub": (REG, 52, 1.35), "num": (BOLD, 170, 1.0),
         "head": (BOLD, 86, 1.15), "body": (REG, 50, 1.4), "btn": (BOLD, 54, 1.0)}


def layout(items):
    """Return [(kind, lines, font, color_key, height)] and the total block height."""
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    rows, total = [], 0
    for kind, text, color in items:
        names, size, gap = STYLE[kind]
        f = font(names, size)
        lines = [text] if kind in ("num", "btn") else wrap(probe, text, f, MAX_W)
        h = int(len(lines) * size * gap) + (40 if kind != "num" else 10)
        if kind == "btn":
            h = 150
        rows.append((kind, lines, f, color, h))
        total += h
    return rows, total


def draw_scene(bg, rows, total, frame, brand, scene_idx, n_scenes):
    c = brand["colors"]
    img = bg.copy()
    d = ImageDraw.Draw(img, "RGBA")
    d.text((PAD, 130), brand["name"].upper(), font=font(BOLD, 48), fill=hex_rgb(c["accent2"]))
    d.rectangle((0, 0, VW, 10), fill=hex_rgb(c["muted"]) + (60,))
    prog = (scene_idx + frame / (SCENE_SECONDS * FPS)) / n_scenes
    d.rectangle((0, 0, int(VW * prog), 10), fill=hex_rgb(c["accent2"]))
    y = 330 + max(0, (900 - total) // 2)
    for k, (kind, lines, f, ckey, h) in enumerate(rows):
        t = min(1.0, max(0.0, (frame - k * 8) / FADE_FRAMES))
        t = 1 - (1 - t) ** 3  # ease out
        alpha = int(255 * t)
        dy = int(SLIDE_PX * (1 - t))
        col = hex_rgb(c[ckey])
        if kind == "btn":
            d.rounded_rectangle((PAD, y + dy, PAD + 600, y + dy + 120), 60, fill=col + (alpha,))
            d.text((PAD + 70, y + dy + 30), lines[0], font=f, fill=hex_rgb(c["text"]) + (alpha,))
        else:
            ly = y + dy
            for line in lines:
                d.text((PAD, ly), line, font=f, fill=col + (alpha,))
                ly += int(f.size * STYLE[kind][2])
        y += h
    d.text((PAD, VH - 380), f"{brand['handle']}  |  {brand['tagline']}", font=font(REG, 36),
           fill=hex_rgb(c["muted"]) + (200,))
    return img.convert("RGB")


def render_video(content, brand, out_path):
    out_path = Path(out_path)
    c = brand["colors"]
    bg = gradient(c["bg_top"], c["bg_bottom"], (VW, VH))
    all_scenes = scenes(content, brand)
    frames_per = int(SCENE_SECONDS * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{VW}x{VH}", "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264",
         "-pix_fmt", "yuv420p", "-profile:v", "high", "-crf", "20", "-movflags", "+faststart",
         str(out_path)], stdin=subprocess.PIPE)
    for si, items in enumerate(all_scenes):
        rows, total = layout(items)
        for fr in range(frames_per):
            ff.stdin.write(draw_scene(bg, rows, total, fr, brand, si, len(all_scenes)).tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg failed")
    return out_path
