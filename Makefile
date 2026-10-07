# ============================================================
# beamer deck 三模式编译
#   make            build/VeriNC-slides.pdf                放映版
#   make dual       build/VeriNC-slides-with-script.pdf    右半为讲稿，勿直接投影
#   make notes      build/VeriNC-script.pdf                纯讲稿，导手机/平板
#   make pptx       build/VeriNC-ICNP26.pptx               讲稿进备注栏
#   make figures    把 figures/*.svg 增量转成矢量 PDF
#   make watch      监听改动持续重编（CLI 版热重载）
#   make clean      清掉中间文件
# ============================================================
LATEXMK := latexmk
# 脚本全在 tools/ 里，随包走——这份 deck 换台机器也能整套跑起来
TOOLS   := tools
# beamer 的 show-notes-on-second-screen 会把讲稿页的颜色漏进下一张幻灯片，
# 正文文字变白（详见 beamer_fix_dual.py 的说明）。用放映版的页面盖回去。
FIXDUAL := $(wildcard $(TOOLS)/beamer_fix_dual.py)
# PDF 每页转成一张整页图片，讲稿写进备注栏。版式不会重排、字体不会替换。
PDF2PPTX:= $(wildcard $(TOOLS)/pdf2pptx.py)
SRC     := main.tex
OUT     := build
# 产物直接叫交付时的名字，免得「我编出来的 main.pdf 是哪一份」
SLIDES  := VeriNC-slides
DUAL    := VeriNC-slides-with-script
SCRIPT  := VeriNC-script
PPTX    := VeriNC-ICNP26
# pptx 的中间页（讲稿只留本页那块的双宽 PDF），不是交付物
PPTXPDF := pptx-pages

SVGS    := $(wildcard figures/*.svg)
FIGPDFS := $(SVGS:.svg=.pdf)
# 讲稿写在 speech.md，编译时自动灌进 \note{}
NOTES   := $(wildcard speech.md)
NOTESTEX:= $(NOTES:speech.md=speech-notes.tex)

.PHONY: all slides dual notes pptx figures watch clean

all: slides

slides: figures $(NOTESTEX)
	$(LATEXMK) -jobname=$(SLIDES) $(SRC)

dual: slides
	$(LATEXMK) -jobname=$(DUAL) -pretex='\def\notemode{dual}' -usepretex $(SRC)
	$(if $(FIXDUAL),uv run $(FIXDUAL) $(OUT)/$(DUAL).pdf $(OUT)/$(SLIDES).pdf,\
	  @echo "警告：缺 beamer_fix_dual.py，幻灯片半边正文会发白")
# 讲稿页是静默截断的，台上翻到那一步才发现话没了——所以每次出 dual 都机器查一遍
	uv run $(TOOLS)/checknotes.py $(OUT)/$(DUAL).pdf

# PowerPoint 的演讲者视图不保留字体颜色，dual 版那种「当前块黑、其余灰」
# 在里面全变成同一个色，一整段堆在一起反而定位不到该念哪句。
# 所以这一版走 \notemode{pptx}：讲稿页每页只放本页该念的那一块。
pptx: slides
	$(LATEXMK) -jobname=$(PPTXPDF) -pretex='\def\notemode{pptx}' -usepretex $(SRC)
	$(if $(FIXDUAL),uv run $(FIXDUAL) $(OUT)/$(PPTXPDF).pdf $(OUT)/$(SLIDES).pdf,)
	$(if $(PDF2PPTX),uv run $(PDF2PPTX) $(OUT)/$(PPTXPDF).pdf -o $(OUT)/$(PPTX).pptx,\
	  @echo "警告：缺 pdf2pptx.py，跳过 pptx 生成")
	$(if $(PDF2PPTX),uv run $(TOOLS)/pptx_notes.py $(OUT)/$(PPTX).pptx speech.md,)
# 讲稿已由 speech.md 重写进备注栏，这份双宽中间页没有保留价值，别和成品混在一起
	$(if $(PDF2PPTX),rm -f $(OUT)/$(PPTXPDF).pdf,)

notes: figures $(NOTESTEX)
	$(LATEXMK) -jobname=$(SCRIPT) -pretex='\def\notemode{notes}' -usepretex $(SRC)

figures: $(FIGPDFS)

speech-notes.tex: speech.md $(TOOLS)/speech2tex.py
	python3 $(TOOLS)/speech2tex.py $< > $@

# SVG 转矢量 PDF；rsvg-convert 来自 librsvg2-bin，不经过光栅化
figures/%.pdf: figures/%.svg
	rsvg-convert -f pdf -o $@ $<

watch: figures $(NOTESTEX)
	$(LATEXMK) -pvc -jobname=$(SLIDES) $(SRC)

clean:
	$(LATEXMK) -C $(SRC) || true
	rm -rf $(OUT) $(NOTESTEX)
