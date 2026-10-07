#!/usr/bin/env python3
r"""把 speech.md 的 **Pn.** 段落转成 beamer 讲稿宏。

讲稿用 markdown 写（好改、好读），编译时自动灌进 \note{}，
不用手抄进 .tex，也就不会抄错、不会两边不同步。

一段讲稿里写 [>] 就是"这里按一下空格"。带 [>] 的段落会按 overlay
切开：每个 overlay 都显示完整讲稿，但当前该念的那块正常显色、
其余灰掉，面包屑同时给出「动画 2/3」。没有 [>] 的段落行为不变。

用法：python3 speech2tex.py speech.md > speech-notes.tex
帧里：\speechnote{8}      （放在 frame 内部，不要包在 \note{} 里）
      \note{\speech{8}}   （旧写法，仍可用，但没有 overlay 对齐）
"""
import re
import sys

# LaTeX 特殊字符；逐字符查表替换，不会二次转义
ESCAPE = {
    '\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
    '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}',
    '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
}
STEP = re.compile(r'\[>\]')


def esc(text):
    return ''.join(ESCAPE[c] if c in ESCAPE else c for c in text)


def paragraphs(block):
    """空行 = 段落分隔，段内换行只是排版折行 → 合成空格。"""
    paras = [' '.join(p.split()) for p in re.split(r'\n\s*\n', block) if p.strip()]
    return r'\par '.join(esc(p) for p in paras)


def main():
    if len(sys.argv) < 2:
        sys.exit('用法：speech2tex.py <speech.md>')
    with open(sys.argv[1], encoding='utf-8') as fh:
        raw = fh.read()

    # 按 **Pn.** 切开；split 后是 [前言, '1', 正文, '2', 正文, ...]
    parts = re.split(r'^\*\*P(\d+)\.\*\*\s*', raw, flags=re.M)
    if len(parts) < 3:
        sys.exit('speech.md 里没找到 **Pn.** 段落标记')

    numbers = parts[1::2]
    bodies = parts[2::2]
    total = len(numbers)

    out = [r'% 本文件由 speech2tex.py 从 speech.md 生成，勿手改',
           r'\providecommand{\speech}[1]{%',
           r'  \ifcsname speechP#1\endcsname\csname speechP#1\endcsname'
           r'\else\textit{（第 #1 段讲稿缺失）}\fi}',
           r'\providecommand{\speechnote}[1]{%',
           r'  \ifdefstring{\notemode}{pptx}'
           r'{\ifcsname speechS#1\endcsname\csname speechS#1\endcsname'
           r'\else\note{\textit{（第 #1 段讲稿缺失）}}\fi}'
           r'{\ifcsname speechN#1\endcsname\csname speechN#1\endcsname'
           r'\else\note{\textit{（第 #1 段讲稿缺失）}}\fi}}',
           '']

    for num, body in zip(numbers, bodies):
        blocks = [b for b in STEP.split(body.strip()) if b.strip()]
        rendered = [paragraphs(b) for b in blocks]
        steps = len(rendered)

        # 纯文本版：\note{\speech{n}} 的旧写法用这个，没有高亮
        out.append(r'\expandafter\def\csname speechP%s\endcsname{%s}'
                   % (num, r'\par '.join(rendered)))

        # overlay 版：\speechnote{n} 用这个
        head = (r'\gdef\speechindex{%s}\gdef\speechcount{%d}'
                r'\gdef\speechtotal{%d}' % (num, total, steps))
        if steps == 1:
            notes = r'\note{%s}' % rendered[0]
        else:
            notes = ''.join(
                r'\note<%d>{%s}' % (
                    i + 1,
                    r'\par '.join(r'\speechon{%s}' % text if j == i
                                  else r'\speechoff{%s}' % text
                                  for j, text in enumerate(rendered)))
                for i in range(steps))
        out.append(r'\expandafter\def\csname speechN%s\endcsname{%s%s}'
                   % (num, head, notes))

        # 单块版：pptx 模式用。PowerPoint 的演讲者视图丢掉字体颜色，
        # 灰显区分不出当前块，整段堆在一起反而找不到该念哪句——
        # 所以那一版每页只放本页该念的那一块。
        if steps == 1:
            single = r'\note{%s}' % rendered[0]
        else:
            single = ''.join(r'\note<%d>{%s}' % (i + 1, rendered[i])
                             for i in range(steps))
        out.append(r'\expandafter\def\csname speechS%s\endcsname{%s%s}'
                   % (num, head, single))

    print('\n'.join(out))


if __name__ == '__main__':
    main()
