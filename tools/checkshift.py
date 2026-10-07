#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf"]
# ///
r"""查同一帧的相邻 overlay 之间，已经出现过的内容有没有被推着移动。

beamer 的 frame 默认把内容垂直居中，而 `\only` 的内容在还没出现时**不占位**——
于是后面的 overlay 一出现，总高度变了，前面的内容就被推着上移。投影上看就是
翻一页、整块内容跳一下，讲到一半观众的视线要重新找位置。

`\item<n->`、`\visible`、`\uncover` 都是占位的（`\item<n->` 默认按 `\uncover`
处理），没有这个问题；代价是占位内容会把每一页都撑到最大高度，一个 alertblock
能让四页全溢出同样的数值。所以 `\only` 也不是无脑换掉就行。

只在同一帧内部比较（frametitle 相同的连续页）。跨帧的位置差是正常的——不同帧
本来就排不一样，比了只会得到一堆假阳性。

用法：python3 checkshift.py [build/main.pdf]
"""
import sys

import pymupdf

THRESHOLD = 0.5   # pt，小于这个当作排版舍入噪声


def read(page):
    """→ (frametitle, {行文本: 顶边 y})。frametitle 取最顶上那行。"""
    rows = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = " ".join(s["text"] for s in line["spans"]).strip()
            if text:
                rows.append((round(line["bbox"][1], 2), text))
    rows.sort()
    if not rows:
        return "", {}
    body = {}
    for y, text in rows[1:]:
        body.setdefault(text, y)   # 同一行文本重复出现时只记第一次
    return rows[0][1], body


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "build/main.pdf"
    doc = pymupdf.open(path)

    found = []
    prev_no, prev = 0, None
    for no, page in enumerate(doc, 1):
        cur = read(page)
        if prev and prev[0] == cur[0]:         # 同一帧的下一个 overlay
            moved = [(t, prev[1][t], y) for t, y in cur[1].items()
                     if t in prev[1] and abs(prev[1][t] - y) > THRESHOLD]
            if moved:
                found.append((prev_no, no, cur[0], moved))
        prev_no, prev = no, cur

    if not found:
        print(f"overlay 位移检查：{len(doc)} 页，同帧翻页没有内容移动")
        return

    print("翻页时上一页的内容被推动了：")
    for a, b, title, moved in found:
        shift = moved[0][2] - moved[0][1]
        title = " ".join(title.split())
        print(f"  第 {a}→{b} 页 · {title[:40]} —— {len(moved)} 行 {shift:+.1f}pt")
        for text, y0, y1 in moved[:2]:
            print(f"      {y0:7.1f} → {y1:7.1f}   {' '.join(text.split())[:52]}")
    print("多半是 \\only 不占位。换成 \\visible / \\uncover，或者给那块一个固定高度"
          "的 minipage；改完回头确认没把页面撑溢出。")


if __name__ == "__main__":
    main()
