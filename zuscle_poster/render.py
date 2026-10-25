"""Render the carousel slides (1080x1350, Instagram 4:5) with Pillow."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
PAD = 90
FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation",
             "/Library/Fonts", "C:/Windows/Fonts"]
BOLD = ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"]
REG = ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "Arial.ttf", "arial.ttf"]


def font(names, size):
    for d in FONT_DIRS:
        for n in names:
            p = Path(d) / n
            if p.exists():
                return ImageFont.truetype(str(p), size)
    return ImageFont.load_default(size)


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def gradient(c1, c2, size=(W, H)):
    w, h = size
    img = Image.new("RGB", size)
    px = ImageDraw.Draw(img)
    a, b = hex_rgb(c1), hex_rgb(c2)
    for y in range(h):
        t = y / (h - 1)
        px.line([(0, y), (w, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    return img


def wrap(draw, text, fnt, max_w):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_block(draw, text, fnt, y, fill, line_gap=1.25):
    for line in wrap(draw, text, fnt, W - 2 * PAD):
        draw.text((PAD, y), line, font=fnt, fill=fill)
        y += int(fnt.size * line_gap)
    return y


def base(brand, page, total):
    c = brand["colors"]
    img = gradient(c["bg_top"], c["bg_bottom"])
    d = ImageDraw.Draw(img)
    d.ellipse((W - 420, -220, W + 220, 420), fill=hex_rgb(c["accent"]) + ())
    img = Image.blend(gradient(c["bg_top"], c["bg_bottom"]), img, 0.18)
    d = ImageDraw.Draw(img)
    d.text((PAD, 80), brand["name"].upper(), font=font(BOLD, 44), fill=hex_rgb(c["accent2"]))
    if total > 1:
        pg = f"{page}/{total}"
        f = font(REG, 34)
        d.text((W - PAD - d.textlength(pg, font=f), 88), pg, font=f, fill=hex_rgb(c["muted"]))
    d.text((PAD, H - 110), f"{brand['handle']}  |  {brand['tagline']}", font=font(REG, 32),
           fill=hex_rgb(c["muted"]))
    return img, d


def cover(content, brand, total):
    c = brand["colors"]
    img, d = base(brand, 1, total)
    y = draw_block(d, content["cover_title"], font(BOLD, 96), 340, hex_rgb(c["text"]), 1.15)
    d.rectangle((PAD, y + 30, PAD + 160, y + 40), fill=hex_rgb(c["accent2"]))
    draw_block(d, content["cover_subtitle"], font(REG, 46), y + 80, hex_rgb(c["muted"]))
    d.text((PAD, H - 200), "Swipe  >", font=font(BOLD, 40), fill=hex_rgb(c["accent"]))
    return img


def tip(slide, n, brand, page, total):
    c = brand["colors"]
    img, d = base(brand, page, total)
    d.text((PAD, 260), f"{n:02d}", font=font(BOLD, 150), fill=hex_rgb(c["accent"]))
    y = draw_block(d, slide["heading"], font(BOLD, 78), 470, hex_rgb(c["text"]), 1.15)
    draw_block(d, slide["body"], font(REG, 44), y + 30, hex_rgb(c["muted"]), 1.4)
    return img


def cta(brand, page, total):
    c = brand["colors"]
    img, d = base(brand, page, total)
    y = draw_block(d, "Train smarter, not harder.", font(BOLD, 92), 380, hex_rgb(c["text"]), 1.15)
    y = draw_block(d, brand["cta"], font(REG, 48), y + 30, hex_rgb(c["muted"]), 1.4)
    d.rounded_rectangle((PAD, y + 50, PAD + 560, y + 160), 55, fill=hex_rgb(c["accent"]))
    d.text((PAD + 55, y + 78), "Link in bio", font=font(BOLD, 46), fill=hex_rgb(c["text"]))
    return img


def render_all(content, brand, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    slides = content["slides"]
    total = len(slides) + 2
    images = [cover(content, brand, total)]
    images += [tip(s, i, brand, i + 1, total) for i, s in enumerate(slides, 1)]
    images.append(cta(brand, total, total))
    paths = []
    for i, im in enumerate(images, 1):
        p = out_dir / f"slide_{i:02d}.jpg"
        im.convert("RGB").save(p, quality=92)
        paths.append(p)
    return paths
