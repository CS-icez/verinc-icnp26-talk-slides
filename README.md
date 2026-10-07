# VeriNC — ICNP 2026 Talk Slides

**VeriNC** is the first general-purpose tool for verifying [in-network computing (INC)](https://en.wikipedia.org/wiki/In-network_computing) systems. By modeling INC protocols and performing model checking, VeriNC identifies design risks that can lead to property violations under network exceptions such as packet loss and out-of-order delivery.

This repository contains the slides for the VeriNC talk at the 34th IEEE International Conference on Network Protocols (ICNP 2026), given in Tempe, Arizona, on October 6, 2026 (Session 3: In-Network Computing & Programmable Switches).

> 📄 **Paper:** Tianyu Bai, Xiaoxi Zhang, Haoqing Wang, Ying Zhang, Wenfei Wu. *VeriNC: Finding Design Risks of In-Network Computing Systems.* IEEE ICNP 2026. [[arXiv]](https://arxiv.org/abs/2604.10186)
>
> 🏆 **ICNP 2026 Best Paper Award**

**Slides:** [VeriNC-ICNP26-slides.pdf](VeriNC-ICNP26-slides.pdf)

The PDF has 34 pages because each slide builds up in several steps; there are 16 distinct slides.

## Related Repositories

- [VeriNC Compiler](https://github.com/CS-icez/VeriNC-Compiler) — Compiler that translates `.inc` protocol specifications into TLA+/PlusCal for model checking.
- [VeriNC Violation](https://github.com/CS-icez/VeriNC-Violation) — Reproduction code for design risks identified by VeriNC in real systems.
- [EPIC](https://github.com/In-Net/EPIC) — An INC protocol specification and reference system built on the principle of "Unified Abstraction, Polymorphic Realization" (SIGCOMM 2026), which uses VeriNC for formal correctness verification.

## Source

The slides are written in LaTeX beamer. Everything besides the PDF above is the source it was built from.

| Path | |
|---|---|
| `main.tex`, `preamble.tex` | Entry point and theme setup. |
| `sections/*.tex` | Slide content, one file per part of the talk. |
| `tikz/*.tex` | The two diagrams drawn for the talk. |
| `figures/workflow.pdf` | The workflow figure from the paper. |
| `speech.md` | Placeholder for the speaking script. |
| `tools/` | Build scripts for the script and PowerPoint outputs. |

The speaking script is not published. `speech.md` keeps its structure — one paragraph per slide, one `[>]` per build step — with every paragraph replaced by a placeholder, because the build reads it to decide how many pages each slide takes.

The comments in the `.tex` files and scripts are in Chinese. They are layout notes and do not affect compilation.

### Building

```bash
make
```

This writes `build/VeriNC-slides.pdf`, identical to the PDF in this repository.

The other targets put the script next to the slides, so here they produce the placeholder text:

| Target | Output in `build/` | Contains |
|---|---|---|
| `make` | `VeriNC-slides.pdf` | slides only |
| `make dual` | `VeriNC-slides-with-script.pdf` | slide left, script right |
| `make notes` | `VeriNC-script.pdf` | script only |
| `make pptx` | `VeriNC-ICNP26.pptx` | slides as images, script in the notes pane |

Requirements:

- TeX Live 2024 or newer, with XeLaTeX and `latexmk`. The `moloch` beamer theme entered TeX Live in 2024, so earlier releases will not have it.
- Packages: `moloch`, `ctex`, `tikz`, `booktabs`, `makecell`, `amsmath`, `amssymb`, `etoolbox`, `listings`, `pifont`.
- Python 3 for `make`. The `dual` and `pptx` targets also need [`uv`](https://docs.astral.sh/uv/), which fetches the scripts' dependencies (`pymupdf`, `python-pptx`) on first run.

A full TeX Live or MacTeX install covers the LaTeX side. On Debian/Ubuntu: `texlive-xetex texlive-latex-extra texlive-fonts-extra texlive-lang-chinese latexmk`.

## Copyright

The slides are © 2026 the authors.

The workflow figure (`figures/workflow.pdf`, page 14 of the slides) is reproduced from the ICNP 2026 paper above and is © 2026 IEEE. Other material drawn from the paper (results, tables, quoted text) is likewise used with attribution to that paper. IEEE does not endorse any product or service mentioned in these slides.

## Citation

If you use VeriNC in your research, please cite:

```bibtex
@inproceedings{bai2026verinc,
  author    = {Bai, Tianyu and Zhang, Xiaoxi and Wang, Haoqing and Zhang, Ying and Wu, Wenfei},
  title     = {{VeriNC}: Finding Design Risks of In-Network Computing Systems},
  booktitle = {2026 IEEE 34th International Conference on Network Protocols (ICNP)},
  year      = {2026}
}
```

The proceedings are not yet on IEEE Xplore, so this entry has no pages or DOI. They will be added once the official record is available.

## Contact

Tianyu Bai — tianyubai@stu.pku.edu.cn
