#!/usr/bin/env python3
"""Compile a TikZ figure into a web-ready, theme-aware inline SVG.

The raw output of `latex` + `dvisvgm` is not safe to paste into a web page:
every figure hardcodes black, carries absolute pt dimensions, and reuses the
same glyph ids (`g0-67`, `page1`, `clip1`). Two such figures on one page
collide on those ids and the second one renders as garbage.

This script fixes all of that in one pass so a figure can be inlined directly:

  * `#000` becomes `currentColor`, so the figure inherits the surrounding text
    color and follows light/dark themes for free.
  * declared accent colors are rewritten to CSS custom properties.
  * every id is namespaced with a per-figure slug.
  * pt width/height are dropped in favor of the viewBox, so the figure scales.
  * `role="img"` plus `<title>`/`<desc>` make it legible to screen readers.

Usage:
    tikz2svg.py figure.tex -o figure.svg \\
        --title "Request lifecycle" \\
        --desc "A request passes through the edge cache before reaching origin." \\
        --map 2F6FEB=--fig-accent --map D14343=--fig-warn
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# A bare `\begin{tikzpicture}` fragment gets wrapped in this. `standalone` crops
# the page to the drawing, and sans-serif matches web body text far better than
# the default Computer Modern serif.
PREAMBLE = r"""\documentclass[dvisvgm,border=2pt]{standalone}
\usepackage[T1]{fontenc}
\renewcommand{\familydefault}{\sfdefault}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,calc,fit,backgrounds,shapes.geometric,shapes.multipart,
  decorations.pathreplacing,decorations.markings,patterns,automata,chains,matrix,shadows.blur}
\begin{document}
%(body)s
\end{document}
"""


def slugify(name: str) -> str:
    """Turn a filename into a short id-safe prefix."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return slug or "fig"


def run_latex(tex_source: str, workdir: Path) -> Path:
    """Compile TeX source to a DVI, raising with a useful excerpt on failure."""
    tex_path = workdir / "figure.tex"
    tex_path.write_text(tex_source, encoding="utf-8")

    proc = subprocess.run(
        ["latex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
        cwd=workdir,
        capture_output=True,
        text=True,
    )
    dvi_path = workdir / "figure.dvi"
    if proc.returncode != 0 or not dvi_path.exists():
        # LaTeX buries the real error in a wall of output; surface the `!` lines.
        errors = [ln for ln in proc.stdout.splitlines() if ln.startswith("!")]
        detail = "\n".join(errors[:10]) or proc.stdout[-1500:]
        raise RuntimeError(f"latex failed:\n{detail}")
    return dvi_path


def run_dvisvgm(dvi_path: Path, workdir: Path) -> str:
    """Convert DVI to SVG, tracing glyphs to paths so no web font is needed."""
    svg_path = workdir / "figure.svg"
    proc = subprocess.run(
        [
            "dvisvgm",
            "--no-fonts",      # glyphs become paths: no font dependency at all
            "--exact-bbox",    # tight crop around the actual ink
            "--relative",      # shorter path data
            f"--output={svg_path}",
            str(dvi_path),
        ],
        cwd=workdir,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not svg_path.exists():
        raise RuntimeError(f"dvisvgm failed:\n{proc.stderr[-1500:]}")
    return svg_path.read_text(encoding="utf-8")


def namespace_ids(svg: str, prefix: str) -> str:
    """Prefix every id and reference so multiple figures can share a page."""
    ids = set(re.findall(r"id=['\"]([^'\"]+)['\"]", svg))
    for ident in sorted(ids, key=len, reverse=True):
        new = f"{prefix}-{ident}"
        svg = re.sub(rf"id=(['\"]){re.escape(ident)}\1", rf"id=\g<1>{new}\g<1>", svg)
        svg = re.sub(rf"href=(['\"])#{re.escape(ident)}\1", rf"href=\g<1>#{new}\g<1>", svg)
        svg = re.sub(rf"url\(#{re.escape(ident)}\)", f"url(#{new})", svg)
    return svg


def themeify(svg: str, color_map: dict[str, str]) -> str:
    """Swap hardcoded hex colors for currentColor and CSS custom properties."""
    # Black is the figure's "ink" — inheriting currentColor makes the whole
    # drawing follow the surrounding text color in both themes.
    svg = re.sub(r"(fill|stroke)=(['\"])#000(?:000)?\2", r"\1=\g<2>currentColor\g<2>", svg, flags=re.I)

    for hex_value, css_var in color_map.items():
        bare = hex_value.lstrip("#").lower()
        short = bare[0::2] if len(bare) == 6 and bare[0] == bare[1] and bare[2] == bare[3] and bare[4] == bare[5] else None
        alternatives = [bare] + ([short] if short else [])
        for alt in alternatives:
            svg = re.sub(
                rf"(fill|stroke)=(['\"])#{alt}\2",
                rf"\1=\g<2>var({css_var}, #{bare})\g<2>",
                svg,
                flags=re.I,
            )
    return svg


def make_responsive(svg: str, css_class: str) -> str:
    """Drop absolute pt sizing so the figure scales with its container."""
    svg = re.sub(r"\s(width|height)=['\"][^'\"]*['\"]", "", svg, count=2)
    svg = svg.replace("<svg ", f'<svg class="{css_class}" ', 1)
    return svg


def add_accessibility(svg: str, title: str | None, desc: str | None) -> str:
    """A diagram that carries meaning needs a text equivalent, not alt=''."""
    if not title and not desc:
        return svg
    parts = ['role="img"']
    svg = svg.replace("<svg ", f"<svg {' '.join(parts)} ", 1)

    nodes = ""
    if title:
        nodes += f"\n<title>{escape(title)}</title>"
    if desc:
        nodes += f"\n<desc>{escape(desc)}</desc>"
    return re.sub(r"(<svg[^>]*>)", rf"\1{nodes}", svg, count=1)


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def strip_cruft(svg: str) -> str:
    """Remove the XML declaration and generator comments before inlining."""
    svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
    svg = re.sub(r"<!--.*?-->\s*", "", svg, flags=re.S)
    return svg.strip()


def check_tooling() -> None:
    missing = [tool for tool in ("latex", "dvisvgm") if shutil.which(tool) is None]
    if missing:
        raise SystemExit(
            f"missing required tool(s): {', '.join(missing)}\n"
            "Install a TeX distribution with TikZ and dvisvgm, e.g.\n"
            "  Debian/Ubuntu: apt-get install texlive-latex-base texlive-latex-extra "
            "texlive-pictures texlive-fonts-recommended dvisvgm\n"
            "  macOS:         brew install --cask mactex-no-gui  (or basictex)\n"
            "See references/pipeline.md for a no-LaTeX fallback."
        )


def compile_figure(
    tex_source: str,
    prefix: str,
    color_map: dict[str, str],
    title: str | None,
    desc: str | None,
    css_class: str,
) -> str:
    if "\\documentclass" not in tex_source:
        tex_source = PREAMBLE % {"body": tex_source.strip()}

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        dvi = run_latex(tex_source, workdir)
        svg = run_dvisvgm(dvi, workdir)

    svg = strip_cruft(svg)
    svg = namespace_ids(svg, prefix)
    svg = themeify(svg, color_map)
    svg = make_responsive(svg, css_class)
    svg = add_accessibility(svg, title, desc)
    return svg + "\n"


def parse_map(values: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in values:
        if "=" not in item:
            raise SystemExit(f"--map expects HEX=--css-var, got: {item}")
        hex_value, css_var = item.split("=", 1)
        if not css_var.startswith("--"):
            css_var = "--" + css_var.lstrip("-")
        mapping[hex_value.strip()] = css_var.strip()
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", help="a .tex file: full document or bare tikzpicture")
    parser.add_argument("-o", "--output", help="output .svg path (default: alongside source)")
    parser.add_argument("--title", help="short <title> for screen readers")
    parser.add_argument("--desc", help="longer <desc> describing what the figure shows")
    parser.add_argument("--map", action="append", default=[], metavar="HEX=--VAR",
                        help="map a hex color to a CSS custom property (repeatable)")
    parser.add_argument("--class", dest="css_class", default="tikz-figure", help="class on the root <svg>")
    parser.add_argument("--prefix", help="id namespace (default: derived from filename)")
    parser.add_argument("--stdout", action="store_true", help="print SVG instead of writing a file")
    args = parser.parse_args()

    check_tooling()

    source = Path(args.source)
    if not source.exists():
        raise SystemExit(f"no such file: {source}")

    prefix = args.prefix or slugify(source.stem)
    try:
        svg = compile_figure(
            source.read_text(encoding="utf-8"),
            prefix=prefix,
            color_map=parse_map(args.map),
            title=args.title,
            desc=args.desc,
            css_class=args.css_class,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.stdout:
        sys.stdout.write(svg)
    else:
        out = Path(args.output) if args.output else source.with_suffix(".svg")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(svg, encoding="utf-8")
        print(f"wrote {out} ({len(svg)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
