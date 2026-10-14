"""Validate a manual: image links exist, PNGs are 1920x1080, no obvious secrets/PII in the text.

python check_manual.py docs/<manual>/manual.md [--size 1920x1080] [--allow-email example.com]
Exit code 1 on errors.
"""
import argparse
import re
import struct
import sys
from pathlib import Path

IMG = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
SECRET = re.compile(r"(password|pwd|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S+", re.I)
VAT = re.compile(r"\b(?:IT)?\d{11}\b")
IBAN = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")


def png_size(p: Path):
    with p.open("rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manual")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--allow-email", action="append", default=[], help="allowed e-mail domain (e.g. example.com)")
    a = ap.parse_args()

    md = Path(a.manual)
    text = md.read_text(encoding="utf-8")
    want = tuple(int(v) for v in a.size.split("x"))
    errors, warns = [], []

    for ln, line in enumerate(text.splitlines(), 1):
        for m in IMG.finditer(line):
            ref = m.group(1)
            if re.match(r"^[a-z]+://", ref):
                continue
            p = (md.parent / ref).resolve()
            if not p.exists():
                errors.append(f"{ln}: missing image {ref}")
            elif p.suffix.lower() == ".png":
                s = png_size(p)
                if s != want:
                    errors.append(f"{ln}: {ref} is {s}, expected {want}")
        for m in EMAIL.finditer(line):
            if not any(m.group(0).lower().endswith("@" + d.lower()) for d in a.allow_email):
                errors.append(f"{ln}: e-mail in text: {m.group(0)}")
        if SECRET.search(line):
            errors.append(f"{ln}: possible credential: {SECRET.search(line).group(0)[:20]}...")
        if VAT.search(line) or IBAN.search(line):
            warns.append(f"{ln}: possible VAT/IBAN-like value")

    imgs_dir = md.parent / "images"
    if imgs_dir.exists():
        used = {Path(m.group(1)).name for m in IMG.finditer(text)}
        for p in sorted(imgs_dir.glob("*.png")):
            if p.name not in used:
                warns.append(f"image not referenced: {p.name}")

    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(errors)} error(s), {len(warns)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
