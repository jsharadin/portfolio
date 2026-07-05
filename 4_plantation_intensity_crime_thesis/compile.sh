#!/bin/bash
# Inline table fragments (\input inside tabular breaks the alignment scanner), then compile twice.
cd "$(dirname "$0")"
python3 - << 'PY'
import re
src = open('paper.tex').read()
out = re.sub(r'\\input\{(output/tables/[^}]+)\}',
             lambda m: open(m.group(1) + '.tex').read().rstrip(), src)
open('paper_build.tex', 'w').write(out)
PY
/Library/TeX/texbin/pdflatex -interaction=nonstopmode paper_build.tex > /dev/null
/Library/TeX/texbin/pdflatex -interaction=nonstopmode paper_build.tex > /dev/null
mv paper_build.pdf paper.pdf && rm -f paper_build.*
