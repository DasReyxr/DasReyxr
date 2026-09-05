#!/usr/bin/env python3
"""
Genera cv_color.tex y cv_ats_plain.tex (y sus PDFs) a partir de un unico
data.json. Edita data.json y vuelve a correr este script:

    python3 build.py

Requiere: jinja2 (pip install jinja2 --break-system-packages) y pdflatex.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

HERE = Path(__file__).parent
OUT = HERE / "dist"
OUT.mkdir(exist_ok=True)

TEX_SPECIAL = {
    "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
    "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}", "\\": r"\textbackslash{}",
}
_TEX_RE = re.compile("|".join(re.escape(k) for k in sorted(TEX_SPECIAL, key=len, reverse=True)))


def tex_escape(value):
    return _TEX_RE.sub(lambda m: TEX_SPECIAL[m.group()], str(value))


def bulletjoin(items):
    return r" \textbullet{} ".join(tex_escape(i) for i in items)


def commajoin(items):
    return ", ".join(tex_escape(i) for i in items)


def build():
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))

    env = Environment(
        loader=FileSystemLoader(str(HERE / "templates")),
        block_start_string=r"\BLOCK{",
        block_end_string="}",
        variable_start_string=r"\VAR{",
        variable_end_string="}",
        comment_start_string=r"\#{",
        comment_end_string="}",
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["tex"] = tex_escape
    env.filters["bulletjoin"] = bulletjoin
    env.filters["commajoin"] = commajoin

    targets = {
        "color.tex.jinja": OUT / "cv_color.tex",
        "plain.tex.jinja": OUT / "cv_ats_plain.tex",
    }

    for template_name, out_path in targets.items():
        rendered = env.get_template(template_name).render(**data)
        out_path.write_text(rendered, encoding="utf-8")
        print(f"[ok] wrote {out_path}")

        # Compile to PDF (run twice, harmless for docs with no refs/TOC).
        for _ in range(1):
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(OUT), str(out_path)],
                cwd=str(OUT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        if result.returncode != 0:
            print(f"[FAIL] pdflatex failed for {out_path} (see {out_path.with_suffix('.log')})")
            continue
        print(f"[ok] compiled {out_path.with_suffix('.pdf')}")


if __name__ == "__main__":
    build()
