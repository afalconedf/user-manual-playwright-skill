"""Blur or fill rectangles on a PNG (fallback when CSS/Playwright masks are not enough).

python blur_regions.py in.png --box 1470,300,350,30 [--box x,y,w,h ...] [--mode blur|fill] [--radius 12] [-o out.png]
"""
import argparse
from PIL import Image, ImageDraw, ImageFilter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--box", action="append", required=True, help="x,y,w,h")
    ap.add_argument("--mode", choices=["blur", "fill"], default="blur")
    ap.add_argument("--radius", type=int, default=12)
    ap.add_argument("-o", "--out")
    a = ap.parse_args()

    img = Image.open(a.image).convert("RGB")
    for b in a.box:
        x, y, w, h = (int(v) for v in b.split(","))
        if a.mode == "fill":
            ImageDraw.Draw(img).rectangle([x, y, x + w, y + h], fill=(68, 68, 68))
        else:
            region = img.crop((x, y, x + w, y + h)).filter(ImageFilter.GaussianBlur(a.radius))
            img.paste(region, (x, y))
    img.save(a.out or a.image)


if __name__ == "__main__":
    main()
