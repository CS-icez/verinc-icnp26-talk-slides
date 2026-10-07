# xelatex 是中文（ctex）的硬要求，不能退回 pdflatex
$pdf_mode = 5;
$xelatex = 'xelatex -interaction=nonstopmode -file-line-error -shell-escape %O %S';
$out_dir = 'build';
# 中间文件（aux/log/nav/xdv…）挪到 build/aux，让 build/ 只剩成品——
# 交付的那几份就放在 build/，重新编译会就地覆盖，不会出现两份同名文件
$aux_dir = 'build/aux';
# beamer 的导航文件 + minted/externalize 的缓存目录一并纳入 clean
$clean_ext = 'nav snm vrb run.xml bbl synctex.gz _minted-%R/*';
