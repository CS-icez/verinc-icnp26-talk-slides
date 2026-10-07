#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf"]
# ///
"""Repair the slide half of a beamer "notes on second screen" PDF.

Beamer's `\\setbeameroption{show notes on second screen=right}` leaks a colour
from the note page into the following slide page: text drawn in `normal text`
comes out white and is invisible on the light background. Tables and bare
paragraphs are hit; itemize and blocks survive because they carry their own
colour. This is beamer itself, not the theme — the stock theme does it too,
and none of the usual hooks (AtEndNote, frametitle, background canvas) help.

The slides-only build has no such problem, so the fix is to paste its pages
over the left half of the double-wide pages. The notes column is untouched.

Usage: beamer_fix_dual.py <dual.pdf> <main.pdf>
"""
import os
import sys

import pymupdf


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: beamer_fix_dual.py <dual.pdf> <main.pdf>")
    dual_path, main_path = sys.argv[1], sys.argv[2]

    main_doc = pymupdf.open(main_path)
    dual_doc = pymupdf.open(dual_path)
    if dual_doc.page_count != main_doc.page_count:
        sys.exit(f"page count differs: {dual_path} has {dual_doc.page_count}, "
                 f"{main_path} has {main_doc.page_count}")

    for i, page in enumerate(dual_doc):
        rect = page.rect
        left = pymupdf.Rect(0, 0, rect.width / 2, rect.height)
        page.add_redact_annot(left)     # drop the miscoloured copy outright,
        page.apply_redactions()         # otherwise both layers stay in the file
        page.show_pdf_page(left, main_doc, i)

    # PyMuPDF refuses a non-incremental save over the file it opened
    tmp = dual_path + ".tmp"
    dual_doc.save(tmp, garbage=3, deflate=True)
    pages = dual_doc.page_count
    dual_doc.close()
    main_doc.close()
    os.replace(tmp, dual_path)
    print(f"  {dual_path}: slide half replaced from {main_path} ({pages} pages)")


if __name__ == "__main__":
    main()
