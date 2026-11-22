#!/usr/bin/env python3
"""Build entry.png for news-image-20261122.

Reads stories.json (a list of stories, each with: kicker, headline, panel
— the path of a generated illustration panel image containing NO text) and
composites a 1024x1024 front-page infographic. ALL text is drawn here with
PIL using system fonts, so no text ever comes from an image model.

Layout (1024x1024, newspaper front page):
  header  : masthead + "SUNDAY, 22 NOVEMBER 2026" date line
  lead    : 1 large story, full width
  grid    : 4 stories, 2 columns x 2 rows
  footer  : date + "World news in one image"
Usage: python3 build_image.py stories.json panels_dir output.png
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
BG = (247, 243, 234)      # newsprint off-white
INK = (20, 20, 20)
RED = (178, 34, 34)
RULE = (20, 20, 20)
MUTED = (90, 85, 75)

SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_panel(img, w, h):
    """Center-crop to fill w x h."""
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    img = img.resize((round(iw * scale), round(ih * scale)), Image.LANCZOS)
    x = (img.width - w) // 2
    y = (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def draw_text_block(draw, x, y, max_w, lines, fnt, fill, leading=None):
    if leading is None:
        leading = int(fnt.size * 1.15)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


def main():
    stories_path, panels_dir, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(stories_path) as f:
        stories = json.load(f)
    assert len(stories) == 5, f"expected 5 stories, got {len(stories)}"
    for s in stories:
        assert s["headline"] and s["kicker"] and s["panel"], s

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # --- header ---
    d.text((32, 22), "THE WORLD IN ONE IMAGE", font=font(SERIF_BOLD, 58), fill=INK)
    d.text((32, 92), "SUNDAY, 22 NOVEMBER 2026", font=font(SANS_BOLD, 40), fill=RED)
    d.text((32, 140), "The day's world news, at a glance", font=font(SANS, 26), fill=MUTED)
    d.line([(32, 180), (992, 180)], fill=RULE, width=4)

    # --- lead story ---
    lead = stories[0]
    panel = fit_panel(Image.open(os.path.join(panels_dir, lead["panel"])).convert("RGB"), 960, 300)
    img.paste(panel, (32, 196))
    d.rectangle([32, 196, 992, 496], outline=RULE, width=3)
    y = 510
    d.text((32, y), lead["kicker"].upper(), font=font(SANS_BOLD, 24), fill=RED)
    lines = wrap(d, lead["headline"], font(SANS_BOLD, 40), 960)[:2]
    draw_text_block(d, 32, y + 34, 960, lines, font(SANS_BOLD, 40), INK, leading=48)
    d.line([(32, 648), (992, 648)], fill=RULE, width=3)

    # --- grid: 4 stories, 2 x 2 ---
    cell_w, cell_h = 472, 132
    img_h = 104
    for i, s in enumerate(stories[1:]):
        col, row = i % 2, i // 2
        x0 = 32 + col * (cell_w + 16)
        y0 = 664 + row * (cell_h + 16)
        panel = fit_panel(Image.open(os.path.join(panels_dir, s["panel"])).convert("RGB"), 150, img_h)
        img.paste(panel, (x0, y0))
        d.rectangle([x0, y0, x0 + 150, y0 + img_h], outline=RULE, width=2)
        tx = x0 + 162
        d.text((tx, y0), s["kicker"].upper(), font=font(SANS_BOLD, 19), fill=RED)
        lines = wrap(d, s["headline"], font(SANS_BOLD, 25), cell_w - 162)[:3]
        draw_text_block(d, tx, y0 + 26, cell_w - 162, lines, font(SANS_BOLD, 25), INK, leading=29)

    # --- footer ---
    d.line([(32, 992 - 44), (992, 992 - 44)], fill=RULE, width=3)
    d.text((32, 992 - 34), "22 NOVEMBER 2026  •  WORLD NEWS IN ONE IMAGE",
           font=font(SANS_BOLD, 22), fill=INK)

    img.save(out_path, "PNG")
    size = os.path.getsize(out_path)
    print(f"wrote {out_path}: {img.size} PNG {size} bytes")
    if size > 1048576:
        # Fall back to JPEG bytes (the gate tells PNG/JPEG apart by magic
        # bytes; the name stays entry.png either way).
        img.convert("RGB").save(out_path, "JPEG", quality=88, optimize=True)
        size = os.path.getsize(out_path)
        print(f"over 1 MiB as PNG, saved as JPEG: {size} bytes")
    assert os.path.getsize(out_path) <= 1048576, "still over 1 MiB"


if __name__ == "__main__":
    main()
