"""Convert a Markdown manual (with images) to DOCX, starting from a DOCX/DOTX template.

python md_to_docx.py manual.md --template template.docx -o manual.docx [--title T] [--version V] [--author A]
                     [--date D] [--toc] [--h1-page-break] [--table-style "Table Grid"]

Template: styles Title, Heading 1-4, Normal, List Bullet, List Number, Quote, Caption are used when present.
Placeholders {{TITLE}} {{VERSION}} {{DATE}} {{AUTHOR}} are replaced in body/headers/footers.
A paragraph with only {{CONTENT}} marks where the body goes; otherwise content is appended after the template body.
"""
import argparse
import copy
import datetime
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Emu

INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`|!\[[^\]]*\]\([^)]+\)|\[[^\]]+\]\([^)]+\))")
IMG = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
NUM_ITEM = re.compile(r"^\s*(\d+)[.)]\s+(.*)")
MISSING = []  # image refs not found; main() reports them and exits 1


def style(doc, name):
    try:
        return doc.styles[name]
    except KeyError:
        return None


def set_style(par, doc, *names):
    for n in names:
        s = style(doc, n)
        if s is not None:
            par.style = s
            return


def text_width(doc):
    sec = doc.sections[-1]
    return sec.page_width - sec.left_margin - sec.right_margin


def add_runs(par, text, doc, base: Path):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            par.add_run(part[2:-2]).bold = True
        elif part.startswith("`") and part.endswith("`"):
            r = par.add_run(part[1:-1])
            r.font.name = "Consolas"
        elif part.startswith("!["):
            add_image(doc, part, base)
        elif part.startswith("[") and LINK.fullmatch(part):
            label, url = LINK.fullmatch(part).groups()
            par.add_run(label if label == url else f"{label} ({url})")
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            par.add_run(part[1:-1]).italic = True
        else:
            par.add_run(part)


def add_image(doc, md_img, base: Path, caption=True):
    m = IMG.fullmatch(md_img.strip())
    if not m:
        return
    alt, ref = m.groups()
    path = (base / ref).resolve()
    if not path.exists():
        MISSING.append(ref)
        doc.add_paragraph(f"[missing image: {ref}]")
        return
    doc.add_picture(str(path), width=Emu(int(text_width(doc))))
    if caption and alt:
        c = doc.add_paragraph(alt)
        set_style(c, doc, "Caption")


def add_toc(doc):
    p = doc.add_paragraph()
    run = p.add_run()
    for kind, txt in (("begin", None), (None, 'TOC \\o "1-3" \\h \\z \\u'), ("separate", None)):
        if kind:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = txt
        run._r.append(el)
    run.add_text("Right-click and choose 'Update field' to build the table of contents.")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(end)


def add_table(doc, rows, table_style, base: Path):
    rows = [r for r in rows if not re.fullmatch(r"\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*", r)]
    cells = []
    for r in rows:
        parts = re.split(r"(?<!\\)\|", r.strip())
        if not parts[0].strip():
            parts = parts[1:]
        if not parts[-1].strip():
            parts = parts[:-1]
        cells.append([c.strip().replace("\\|", "|") for c in parts])
    ncol = max(len(r) for r in cells)
    t = doc.add_table(rows=len(cells), cols=ncol)
    s = style(doc, table_style)
    if s is not None:
        t.style = s
    for i, r in enumerate(cells):
        for j in range(ncol):
            cell = t.cell(i, j)
            par = cell.paragraphs[0]
            add_runs(par, r[j] if j < len(r) else "", doc, base)
            if i == 0:
                for run in par.runs:
                    run.bold = True


def replace_placeholders(doc, values):
    def fix(par):
        full = "".join(r.text for r in par.runs)
        if "{{" not in full:
            return
        new = full
        for k, v in values.items():
            new = new.replace("{{%s}}" % k, v)
        if new != full and par.runs:
            par.runs[0].text = new
            for r in par.runs[1:]:
                r.text = ""

    def walk(container):
        for p in container.paragraphs:
            fix(p)
        for t in getattr(container, "tables", []):
            for row in t.rows:
                for c in row.cells:
                    walk(c)

    walk(doc)
    for sec in doc.sections:
        for part in (sec.header, sec.footer, sec.first_page_header, sec.first_page_footer):
            walk(part)


def clear_body_keep_sectpr(doc):
    body = doc.element.body
    for el in list(body):
        if el.tag != qn("w:sectPr"):
            body.remove(el)


def find_content_marker(doc):
    for p in doc.paragraphs:
        if p.text.strip() == "{{CONTENT}}":
            return p
    return None


def new_list_num(doc, start):
    # new w:num on the List Number abstract list, restarting at `start`; None if the style has no numbering
    s = style(doc, "List Number")
    pPr = s.element.pPr if s is not None else None
    if pPr is None or pPr.numPr is None or pPr.numPr.numId is None:
        return None
    numbering = doc.part.numbering_part.element
    base = numbering.num_having_numId(pPr.numPr.numId.val)
    if base is None:
        return None
    new_id = max(int(n.get(qn("w:numId"))) for n in numbering.findall(qn("w:num"))) + 1
    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(new_id))
    num.append(copy.deepcopy(base.find(qn("w:abstractNumId"))))
    ov = OxmlElement("w:lvlOverride")
    ov.set(qn("w:ilvl"), "0")
    so = OxmlElement("w:startOverride")
    so.set(qn("w:val"), str(start))
    ov.append(so)
    num.append(ov)
    base.addnext(num)
    return new_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("markdown")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--template")
    ap.add_argument("--title")
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--author", default="")
    ap.add_argument("--date", default=datetime.date.today().strftime("%d/%m/%Y"))
    ap.add_argument("--toc", action="store_true")
    ap.add_argument("--h1-page-break", action="store_true")
    ap.add_argument("--table-style", default="Table Grid")
    a = ap.parse_args()

    md_path = Path(a.markdown)
    base = md_path.parent
    lines = md_path.read_text(encoding="utf-8").splitlines()

    doc = Document(a.template) if a.template else Document()
    h1 = next((l[2:].strip() for l in lines if l.startswith("# ")), md_path.stem)
    values = {"TITLE": a.title or h1, "VERSION": a.version, "DATE": a.date, "AUTHOR": a.author}

    marker = find_content_marker(doc)
    tail = []
    if marker is not None:
        body = doc.element.body
        children = list(body)
        idx = children.index(marker._p)
        tail = [e for e in children[idx + 1:] if e.tag != qn("w:sectPr")]
        for e in tail:
            body.remove(e)
        body.remove(marker._p)
    elif not a.template:
        t = doc.add_paragraph(values["TITLE"])
        set_style(t, doc, "Title")

    skip_first_h1 = a.template is None
    in_code = False
    code_buf = []
    table_buf = []
    seen_h1 = False
    toc_done = not a.toc
    num_id = None  # current numbered-list run; blank lines keep it, any other line ends it

    def flush_table():
        nonlocal table_buf
        if table_buf:
            add_table(doc, table_buf, a.table_style, base)
            doc.add_paragraph()
            table_buf = []

    for raw in lines:
        line = raw.rstrip()
        if line.strip() and not NUM_ITEM.match(line):
            num_id = None
        if line.startswith("```"):
            if in_code:
                p = doc.add_paragraph("\n".join(code_buf))
                for r in p.runs:
                    r.font.name = "Consolas"
                code_buf, in_code = [], False
            else:
                flush_table()
                in_code = True
            continue
        if in_code:
            code_buf.append(raw)
            continue
        if line.startswith("|"):
            table_buf.append(line)
            continue
        flush_table()
        if not line.strip() or re.fullmatch(r"-{3,}|\*{3,}", line.strip()):
            continue
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            if level == 1 and not seen_h1:
                seen_h1 = True
                if skip_first_h1:
                    if not toc_done:
                        add_toc(doc)
                        toc_done = True
                    continue
                p = doc.add_paragraph(m.group(2))
                set_style(p, doc, "Title", "Heading 1")
            else:
                if level == 1 and a.h1_page_break:
                    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
                p = doc.add_paragraph()
                add_runs(p, m.group(2), doc, base)
                set_style(p, doc, f"Heading {min(level, 4)}")
            if not toc_done:
                add_toc(doc)
                toc_done = True
            continue
        if line.lstrip().startswith(">"):
            p = doc.add_paragraph()
            add_runs(p, line.lstrip()[1:].strip(), doc, base)
            set_style(p, doc, "Quote", "Intense Quote")
            continue
        m = re.match(r"^\s*[-*+]\s+(.*)", line)
        if m:
            p = doc.add_paragraph()
            add_runs(p, m.group(1), doc, base)
            set_style(p, doc, "List Bullet")
            continue
        m = NUM_ITEM.match(line)
        if m:
            if num_id is None:
                num_id = new_list_num(doc, int(m.group(1)))
            p = doc.add_paragraph()
            add_runs(p, m.group(2), doc, base)
            set_style(p, doc, "List Number")
            if num_id is not None:
                numPr = p._p.get_or_add_pPr().get_or_add_numPr()
                numPr.get_or_add_ilvl().val = 0
                numPr.get_or_add_numId().val = num_id
            continue
        if IMG.fullmatch(line.strip()):
            add_image(doc, line.strip(), base)
            continue
        p = doc.add_paragraph()
        add_runs(p, line.strip(), doc, base)
        set_style(p, doc, "Body Text", "Normal")
    flush_table()

    body = doc.element.body
    sect = body.find(qn("w:sectPr"))
    for e in tail:
        if sect is not None:
            sect.addprevious(e)
        else:
            body.append(e)

    replace_placeholders(doc, values)
    doc.save(a.out)
    print(f"written {a.out}")
    for ref in MISSING:
        print(f"ERROR missing image: {ref}", file=sys.stderr)
    if MISSING:
        sys.exit(1)


if __name__ == "__main__":
    main()
