# tikz-figures

A Claude Code plugin that replaces decorative icons on technical web pages with
real explanatory diagrams — authored as TikZ by a subagent and compiled to
theme-aware inline SVG.

## The idea

Ask a model for a technical landing page and you reliably get three feature cards,
each with a Lucide icon: a shield for "secure", a lightning bolt for "fast", a
database for "scalable". The icons are tasteful and carry no information. A
lightning bolt is not an argument that your system is fast.

The fix is to draw the thing being claimed. If the page says requests are served
from the edge, draw the request path and show where it stops. TikZ is the right
notation for it — declarative and relative, so layouts survive a label getting
longer, with precise geometry that reads as engineered rather than doodled. And
because authoring a figure is a noisy compile-look-fix loop, each figure is
delegated to a subagent, so the LaTeX logs stay out of the page you are building.

See [`demos/`](demos/) for the same page built both ways.

## Layout

```
plugins/tikz-figures/
├── .claude-plugin/plugin.json
├── agents/tikz-figure-artist.md      one figure per subagent
├── commands/tikz-figure.md           /tikz-figure
└── skills/tikz-figure/
    ├── SKILL.md                      when to draw, how to brief, design rules
    ├── references/recipes.md         7 compiling archetypes
    ├── references/pipeline.md        install, flags, troubleshooting
    └── scripts/tikz2svg.py           TikZ → web-ready SVG
demos/
├── PROMPT.md                         the shared prompt and the one added line
├── slop/index.html                   icons
└── with-tikz/index.html              figures
```

## Install

```bash
/plugin marketplace add i-habib/temp
/plugin install tikz-figures@habib-tools
```

Then ask for a diagram, or run `/tikz-figure the request path in the hero`.

The compile step needs a TeX toolchain:

```bash
apt-get install -y texlive-latex-base texlive-latex-extra \
                   texlive-pictures texlive-fonts-recommended dvisvgm
```

`texlive-latex-extra` is required — it provides `standalone.cls`.

## The script

`scripts/tikz2svg.py` runs `latex` → `dvisvgm`, then rewrites the output so it is
safe to inline. That rewriting is the point: raw `dvisvgm` output hardcodes black,
carries fixed `pt` dimensions, and reuses ids like `g0-67` across every figure —
so a page with two diagrams renders the second one as garbage. The script maps
black to `currentColor`, maps accent hexes to CSS custom properties, namespaces
every id, drops the fixed sizing, and adds `role="img"` with `<title>`/`<desc>`.

```bash
python3 scripts/tikz2svg.py figures/request-path.tex \
    --title "Request path through the edge cache" \
    --desc "A request hits the edge worker, which serves from cache or forwards to origin." \
    --map 2F6FEB=--fig-accent
```

One figure, one theme, both modes — the ink inherits the container's color.

## Scope

Diagrams are for mechanisms: parts, ordering, flow, state. Icons remain correct
for navigation, dense list rows, brand marks, and status dots, and the skill says
so. The claim is not that icons are bad — it is that an icon standing in for a
mechanism is a missed explanation.
