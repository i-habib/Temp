# Demos: the same page, twice

Two builds of one landing page for a fictional embedded time-series database.
Same prompt, same copy, same palette, same layout. One instruction differs — see
[`PROMPT.md`](PROMPT.md).

| | |
|---|---|
| [`slop/index.html`](slop/index.html) | Default output. Three feature cards with Lucide icons. |
| [`with-tikz/index.html`](with-tikz/index.html) | Icons replaced with three compiled TikZ figures. |

Open both side by side. Neither is ugly — that is deliberate. If the baseline
were badly designed the comparison would prove nothing, because the fix would
just be "design it better." Both pages are competent; the difference is whether a
reader can learn anything from them.

## What to look at

**The three cards in `slop/`.** "Blazing-fast ingest", "Efficient storage",
"Lightning queries", each above a paragraph that restates the heading. A
lightning bolt, a database cylinder, a magnifier. Every one of those glyphs would
work equally well on a page about a CDN, a queue, or a payments API — which is
another way of saying none of them is about *this* product. The page below them
describes a genuinely interesting storage engine, and the reader has to construct
it in their head from prose alone.

**The three figures in `with-tikz/`.** The write actually forks to two
destinations. The block actually has four regions, and the one read first is at
the end. Four of six blocks are visibly skipped. A reader who studies these knows
how the engine works; a reader who studies the icons knows the product has
opinions about speed.

The prose is byte-identical between the two files. Nothing was added to make the
second version more informative — the same sentences simply became legible.

## Reproducing the figures

The figures are compiled, not hand-drawn. Sources live in
[`with-tikz/figures/`](with-tikz/figures/) as `.tex` next to their `.svg`:

```bash
cd with-tikz/figures
for f in *.tex; do
  python3 ../../../plugins/tikz-figures/skills/tikz-figure/scripts/tikz2svg.py \
    "$f" --map 2F6FEB=--fig-accent
done
```

Both pages are self-contained HTML with no external requests, and both follow the
system light/dark setting. The figures track it for free: their ink is
`currentColor` and their accent is `var(--fig-accent)`, so there is one asset per
figure rather than one per theme.

## The honest caveats

- **This costs a build step.** You need a TeX toolchain, and each figure takes a
  few compile-and-look rounds. For a page that will be read many times, that is a
  good trade; for a throwaway internal page it may not be.
- **Icons are not the enemy.** The nav in `with-tikz/` still has a GitHub mark,
  and it should. The claim is narrower than "icons are slop": an icon standing in
  for a *mechanism* is the failure case, because mechanisms have structure and
  icons cannot carry it.
- **A bad diagram is worse than an icon.** Three vague boxes labeled "Service A"
  waste more of a reader's attention than a lightning bolt does. The figure has
  to be built from real component names and real relationships, which is why the
  skill spends most of its length on what to put in the brief.
