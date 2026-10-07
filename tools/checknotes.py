#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf"]
# ///
r"""每个讲稿页的最后一句，必须能在 speech.md 里找到对应的段落结尾。

讲稿页是静默截断的：排不下的部分直接没了，PDF 里看不出少了东西，台上翻到那一步
才发现要念的话不在屏幕上。所以这里机器查一遍。

用法：python3 checknotes.py [build/dual.pdf]
"""
import re
import sys

import pymupdf

TAIL = 24   # 比对每块末尾多少个字符

# 讲稿页顶上的面包屑由 preamble.tex 的 note page 模板排出，用词取自
# \crumbnote / \crumbstep，中英文两套都认。
CRUMB = re.compile(r"(?:note|讲稿)\s*(\d+)/")


def norm(text):
    """规范化到可以直接比对的形式。

    空白全部去掉，不是压缩：pymupdf 从 PDF 里取中文时会在字与字之间插空格
    （"第二块" 提取出来是 "第 二 块"），只压缩空格仍然对不上 speech.md 的原文。
    引号和破折号也统一：LaTeX 会把 ' 排成 U+2019、-- 排成 en dash，而 speech.md
    里 markdown 式的反引号 `code` 会被排成左单引号 U+2018——两边都归一化成 '。
    """
    for a, b in [("’", "'"), ("‘", "'"), ("`", "'"),
                 ("“", '"'), ("”", '"'),
                 ("—", ""), ("–", ""), ("-", "")]:
        text = text.replace(a, b)
    return "".join(text.split())


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "build/dual.pdf"
    doc = pymupdf.open(path)
    md = open("speech.md", encoding="utf-8").read()

    # 每个 **Pn.** 段落按 [>] 分块，记下每块末尾的一小段
    blocks = {}
    for m in re.finditer(r"\*\*P(\d+)\.\*\*(.*?)(?=\*\*P\d+\.\*\*|\Z)", md, re.S):
        parts = [p for p in m.group(2).split("[>]") if p.strip()]
        blocks[int(m.group(1))] = [norm(p)[-TAIL:] for p in parts]

    bad, checked = [], 0
    for pno, page in enumerate(doc, 1):
        r = page.rect
        notes = page.get_text(clip=pymupdf.Rect(r.width / 2, 0, r.width, r.height))
        m = CRUMB.search(notes)
        if not m:
            continue
        para = int(m.group(1))
        if para not in blocks:
            continue
        flat = norm(notes)
        # 结束页没有 \speechnote，正文是空的，但面包屑里 \speechindex 还留着
        # 上一帧的值——这种页跳过，否则会拿上一帧的讲稿去要求它
        body = flat[m.end():] if m.end() < len(flat) else ""
        if len(body) < 10:
            continue
        checked += 1
        for i, tail in enumerate(blocks[para]):
            if tail not in flat:
                bad.append((pno, para, i + 1, tail))

    if bad:
        print("讲稿被截断的页：")
        seen = set()
        for pno, para, bi, tail in bad:
            if (para, bi) in seen:
                continue
            seen.add((para, bi))
            print(f"  PDF 第 {pno} 页 · 讲稿 P{para} 第 {bi} 块结尾丢失：...{tail}")
    elif checked:
        print(f"讲稿页完整：查了 {checked} 页，没有被截断的块")
    else:
        sys.exit("没有一页匹配上面包屑——检查逻辑和讲稿页模板已经对不上了")


if __name__ == "__main__":
    main()
