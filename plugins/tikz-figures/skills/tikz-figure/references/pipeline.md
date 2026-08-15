# The compile pipeline

## What the script does and why

`scripts/tikz2svg.py` runs `latex` → DVI → `dvisvgm` → SVG, then rewrites the
result so it can be pasted straight into a page.

The rewriting is the important part. Raw `dvisvgm` output is *not* safe to inline:

| Raw output | Problem on a web page | What the script does |
|---|---|---|
| `stroke='#000'` | Invisible in dark mode | → `currentColor` |
| `id='g0-67'`, `id='page1'` | **Two figures on one page collide** and the second renders as garbage | Namespaced to `slug-g0-67` |
| `width='176pt' height='25pt'` | Fixed size, ignores its container | Removed; `viewBox` drives scaling |
| Accent hardcoded as hex | Cannot follow the site's palette | → `var(--fig-accent, #2f6feb)` |
| No text alternative | Unreadable to screen readers | `role="img"` + `<title>`/`<desc>` |

The id collision is the one that bites hardest, because a single figure looks
perfect in isolation and only breaks once a second figure joins the page.

Glyphs are traced to outlines (`--no-fonts`), so a figure carries no font
dependency and renders identically everywhere. The cost is that text in the SVG
is not selectable — an acceptable trade for a diagram, and the `<desc>` covers
accessibility.

## Installing

```bash
# Debian / Ubuntu
apt-get install -y texlive-latex-base texlive-latex-extra \
                   texlive-pictures texlive-fonts-recommended dvisvgm

# macOS
brew install --cask basictex && brew install dvisvgm
# then: sudo tlmgr install standalone pgf

# Fedora
dnf install texlive-scheme-medium texlive-standalone dvisvgm
```

`texlive-latex-extra` is required, not optional — it provides `standalone.cls`,
and without it every compile fails with `File 'standalone.cls' not found`.

Verify with:

```bash
echo '\begin{tikzpicture}\draw (0,0)--(1,1);\end{tikzpicture}' > /tmp/t.tex
python3 scripts/tikz2svg.py /tmp/t.tex --stdout | head -3
```

## Usage

```bash
python3 scripts/tikz2svg.py FIGURE.tex [options]
```

| Option | Purpose |
|---|---|
| `-o PATH` | Output file (default: source path with `.svg`) |
| `--stdout` | Print the SVG instead of writing it |
| `--title` | Short `<title>` — the figure's one-line meaning |
| `--desc` | Longer `<desc>` describing what the figure shows |
| `--map HEX=--VAR` | Map a hex color to a CSS variable; repeatable |
| `--class NAME` | Class on the root `<svg>` (default `tikz-figure`) |
| `--prefix SLUG` | Id namespace (default: derived from the filename) |

The input may be a full `\documentclass` document or a bare `tikzpicture`. Bare
pictures get the bundled preamble, which loads `arrows.meta`, `positioning`,
`calc`, `fit`, `backgrounds`, `shapes.geometric`, `shapes.multipart`,
`decorations.pathreplacing`, `decorations.markings`, `patterns`, `automata`,
`chains`, `matrix`, and `shadows.blur`, and switches the default family to
sans-serif. Write a full document only if you need a package beyond those.

## Building several figures

Give each figure its own `.tex` and compile in a loop. Distinct filenames matter:
the filename becomes the id namespace.

```bash
for f in figures/*.tex; do
  python3 scripts/tikz2svg.py "$f" -o "${f%.tex}.svg" --map 2F6FEB=--fig-accent
done
```

Commit the `.tex` next to the `.svg`. The source is what makes the figure
editable later; an SVG full of traced outlines is effectively write-only.

## Troubleshooting

**`File 'standalone.cls' not found`** — install `texlive-latex-extra`.

**`Undefined control sequence` on a TikZ key** — the library is missing. Check
the preamble list above; if what you need is absent, write a full document with
your own `\usetikzlibrary{...}`.

**`Dimension too large`** — usually a `calc` expression dividing by zero, or
coordinates in the thousands. Work in mm and keep figures under ~200mm wide.

**Figure renders but is invisible on the page** — the container has no `color`.
Since the ink is `currentColor`, an unset color inherits whatever the parent has.
Set `color` on the wrapper.

**Accent didn't become a CSS variable** — `--map` matches the hex `dvisvgm`
emitted, which comes from `\definecolor{...}{HTML}{2F6FEB}`. If you defined the
color with `rgb` or a named `xcolor` value, the emitted hex may differ; grep the
SVG for the actual value and map that.

**Second figure on the page is mangled** — id collision, meaning the figures were
compiled with the same `--prefix`. Give them distinct filenames.

## If LaTeX is unavailable

If the environment genuinely cannot install TeX, the honest fallback is to hand
the same figure brief to a subagent and have it write the SVG directly — same
design rules from `SKILL.md` (monochrome plus one accent, `currentColor` ink,
labeled edges, namespaced ids). The result is usually somewhat less precise,
since coordinates get computed by hand instead of by a layout engine, but it
still beats an icon.

Avoid pulling in a client-side TikZ renderer. Those ship a large WebAssembly
payload, support only a subset of TikZ, and make a static diagram depend on
JavaScript at runtime — all to avoid a build step that produces a better artifact.
