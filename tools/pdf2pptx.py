#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf", "python-pptx"]
# ///
"""Turn a slide PDF into a .pptx of full-page images, keeping speaker notes.

For venues where only PowerPoint is available and a PDF viewer isn't.
Each page becomes one slide-sized picture, so the layout is pixel-identical
to the PDF — nothing reflows, no font substitution.

Beamer's `show notes on second screen=right` produces double-wide pages
(slide on the left, script on the right). Those are detected automatically:
the left half becomes the image, the right half is extracted as text and
written into the notes pane.

Usage:
  uv run pdf2pptx.py slides.pdf [-o out.pptx] [--dpi 150] [--notes auto|right|none]
"""
import argparse
import os
import re
import sys
import tempfile

import pymupdf
from pptx import Presentation
from pptx.util import Emu, Inches

EMU_PER_PT = 12700
# A normal 16:9 slide is ~1.78 wide; a notes-on-second-screen page is ~3.56.
DUAL_RATIO_MIN = 2.6
# The beamer note-page template puts a breadcrumb line at the very top of the
# notes column, always ending in a frame number. It belongs to the deck's
# navigation, not to the script, so it is dropped from the notes pane.
HEADER_RE = re.compile(r"(第\s*\d+\s*帧|frame\s*\d+)\s*$", re.I)
# Beamer pages are physically small (a 16:9 frame is only 6.3in wide), and a
# deck that size looks wrong in PowerPoint and renders soft on a projector.
# Scale up to a normal slide width, keeping the source aspect ratio.
SLIDE_WIDTH_IN = 13.333


# CJK and fullwidth punctuation: a line break between two of these is not a
# word boundary, so the lines are joined without a space.
CJK = re.compile(r"[\u3000-\u9fff\uff00-\uffef]")


def join_lines(parts):
    out = ""
    for t in parts:
        if not out:
            out = t
        elif CJK.match(out[-1]) or CJK.match(t[0]):
            out += t
        else:
            out += " " + t
    return out


def notes_text(page, clip, keep_header):
    """Text of the notes column, with the template's breadcrumb line removed.

    Lines are regrouped into paragraphs by vertical gap rather than taken as
    PyMuPDF hands them over. A PDF has no paragraph structure, only positioned
    lines, and on a notes page PyMuPDF puts nearly every line in a block of its
    own — joining those blocks gives a hard break in the middle of every
    sentence, and the notes pane shows one line per paragraph.

    What cannot be recovered here is spacing that was typeset rather than
    stored: an em dash surrounded by space comes back as "succeeded —but the",
    because that space is a kerning decision, not a character. A deck whose
    script lives in speech.md should overwrite the notes from that source
    instead (see pptx_notes.py in the beamer template).
    """
    # Collect line fragments. A change of colour mid-line puts the two halves in
    # different blocks, so one visual line can arrive as several fragments; they
    # are merged back by vertical position before anything else looks at gaps.
    frags = []
    for b in page.get_text("dict", clip=clip)["blocks"]:
        for l in b.get("lines", []):
            t = " ".join(sp["text"] for sp in l["spans"]).strip()
            if t:
                frags.append((l["bbox"][1], l["bbox"][3],
                              l["bbox"][0], l["bbox"][2], t))
    if not frags:
        return ""
    frags.sort()

    grouped = []
    for top, bottom, left, right, text in frags:
        if grouped and abs(grouped[-1][0] - top) <= 2.0:   # same visual line
            prev = grouped[-1]
            prev[2].append((left, right, text))
            grouped[-1] = (prev[0], max(prev[1], bottom), prev[2])
        else:
            grouped.append((top, bottom, [(left, right, text)]))

    rows = []
    for top, bottom, parts in grouped:
        parts.sort()
        line, prev_right = "", None
        for left, right, text in parts:
            if not line:
                line = text
            elif left - prev_right > 2.0:
                # visibly apart on the page (\hfill and friends) — keep them apart
                line += " " + text
            else:
                line = join_lines([line, text])
            prev_right = right
        rows.append((top, bottom, line))

    if not keep_header and HEADER_RE.search(rows[0][2]):
        rows = rows[1:]

    line_h = sorted(b - a for a, b, _ in rows)[len(rows) // 2]
    paras, cur, prev_bottom = [], [], None
    for top, bottom, text in rows:
        # Only an obvious gap starts a new paragraph. Beamer's note pages set no
        # paragraph skip at all, so the space between two paragraphs is the same
        # as between two lines of one; a tight threshold then cuts sentences in
        # half, which is worse than losing the paragraph break.
        if prev_bottom is not None and top - prev_bottom > 1.2 * line_h:
            paras.append(join_lines(cur))
            cur = []
        cur.append(text)
        prev_bottom = bottom
    if cur:
        paras.append(join_lines(cur))
    return clean("\n\n".join(paras))


def clean(text):
    # PDF text carries letter spacing as literal spaces when the font is set
    # loosely; collapse runs so the notes pane does not show "The   Problem".
    text = re.sub(r"[ \t]{2,}", " ", text)
    lines = [ln.rstrip() for ln in text.splitlines()]
    out, blank = [], False
    for ln in lines:
        if ln.strip():
            out.append(ln.strip())
            blank = False
        elif out and not blank:
            out.append("")
            blank = True
    return "\n".join(out).strip()


def convert(src, dst, dpi, notes_mode, keep_header=False):
    doc = pymupdf.open(src)
    if doc.page_count == 0:
        sys.exit("PDF has no pages")

    first = doc[0].rect
    dual = notes_mode == "right" or (
        notes_mode == "auto" and first.width / first.height >= DUAL_RATIO_MIN
    )
    slide_w = first.width / 2 if dual else first.width

    # Render at whatever resolution gives `dpi` at the final slide size
    scale = SLIDE_WIDTH_IN / (slide_w / 72.0)
    render_dpi = round(dpi * scale)

    prs = Presentation()
    prs.slide_width = Inches(SLIDE_WIDTH_IN)
    prs.slide_height = Inches(SLIDE_WIDTH_IN * first.height / slide_w)
    blank_layout = prs.slide_layouts[6]

    with tempfile.TemporaryDirectory() as tmp:
        for i, page in enumerate(doc, 1):
            r = page.rect
            half = r.width / 2 if dual else r.width
            left = pymupdf.Rect(0, 0, half, r.height)

            png = os.path.join(tmp, f"p{i:03d}.png")
            page.get_pixmap(clip=left, dpi=render_dpi).save(png)

            slide = prs.slides.add_slide(blank_layout)
            slide.shapes.add_picture(png, 0, 0, prs.slide_width, prs.slide_height)

            if dual:
                note = notes_text(page, pymupdf.Rect(half, 0, r.width, r.height), keep_header)
                if note:
                    slide.notes_slide.notes_text_frame.text = note

    prs.save(dst)
    doc.close()
    return prs, dual, render_dpi


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("-o", "--output")
    ap.add_argument("--dpi", type=int, default=150,
                    help="effective resolution at final slide size, default 150")
    ap.add_argument("--notes", choices=["auto", "right", "none"], default="auto",
                    help="where speaker notes live in the PDF, default auto")
    ap.add_argument("--keep-header", action="store_true",
                    help="keep the breadcrumb line that the note-page template "
                         "puts above each script (dropped by default)")
    args = ap.parse_args()

    if not os.path.isfile(args.pdf):
        sys.exit(f"Not found: {args.pdf}")
    out = args.output or os.path.splitext(args.pdf)[0] + ".pptx"

    prs, dual, render_dpi = convert(args.pdf, out, args.dpi, args.notes, args.keep_header)
    noted = sum(1 for s in prs.slides if s.has_notes_slide
                and s.notes_slide.notes_text_frame.text.strip())
    size_mb = os.path.getsize(out) / 1024 / 1024
    w_in = prs.slide_width / 914400
    h_in = prs.slide_height / 914400
    print(f"{out}: {len(prs.slides)} slides, {noted} with notes, {size_mb:.1f} MB")
    print(f"  {w_in:.2f}x{h_in:.2f} inch, rendered at {render_dpi} dpi "
          f"(= {args.dpi} dpi at slide size)"
          f"{', dual-page source' if dual else ''}")


if __name__ == "__main__":
    main()
