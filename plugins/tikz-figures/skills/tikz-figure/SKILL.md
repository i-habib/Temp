---
name: tikz-figure
description: >
  Build real explanatory diagrams for technical web pages by delegating each figure to a
  subagent that authors TikZ and compiles it to a theme-aware inline SVG. Use this skill
  whenever you are building or improving a technical website, landing page, docs page,
  README, or blog post that explains a system — architecture, request flow, data pipeline,
  state machine, algorithm, protocol handshake, storage layout, or before/after comparison.
  Reach for it in particular at the moment you are about to add a Lucide/Heroicons/Feather
  icon to a feature card, a shield or database or lightning-bolt glyph, an emoji, or a
  stock illustration to represent a technical concept — those decorate without informing,
  and a diagram of the actual mechanism is almost always the better answer. Also use it
  when asked to "explain this visually", "add a diagram", "make this page less generic",
  or "show how this works".
---

# TikZ figures for technical web pages

## The problem this solves

Ask any model for a technical landing page and you get the same artifact: three
feature cards, each with a rounded square holding a Lucide icon — a shield for
"secure", a lightning bolt for "fast", a database for "scalable". The icons are
tasteful and completely uninformative. A reader who does not already understand
the system learns nothing from them, because a lightning bolt is not an argument
that your system is fast.

The fix is not a better icon. It is to draw the thing you are actually claiming.
If the page says requests are served from the edge, draw the request path and
show where it stops. If it says the index is a B-tree, draw the tree and show a
lookup descending it. A reader who studies that picture ends up knowing something.

This skill produces those figures by writing **TikZ** and compiling it to inline
SVG. TikZ is worth the extra step because it is declarative and relative: you say
"below the parser, aligned with the lexer" rather than nudging pixel coordinates,
so the layout stays consistent when a label grows. It also produces genuinely
precise geometry — real arrowheads that meet real node borders — which is what
separates a figure that looks engineered from one that looks doodled.

## Delegate each figure to a subagent

Authoring a figure is a compile-look-fix loop. TeX errors are verbose, and
inspecting the output means rendering and actually looking at it, often three or
four times before the spacing is right. Running that loop on the main thread
buries the page you are building under LaTeX logs.

So spawn a subagent per figure, and run independent figures in parallel. Each one
returns a small result — a path to an `.svg` and one line about what it shows —
while the noise stays in its own context. If the plugin's `tikz-figure-artist`
agent is available, use it; otherwise a general-purpose subagent works, pointed
at this skill.

**What the subagent needs from you is the actual technical content.** This is
where delegation usually fails. "Make a diagram about our caching layer" produces
a generic three-box drawing that is no better than the icon it replaced. The
subagent cannot see your codebase or your page, so hand it:

- **The claim the figure must support** — the specific sentence on the page it
  sits next to. The figure is an argument for that sentence.
- **The real components and their real names** — `edge-worker`, `pg-primary`,
  `read-replica`, not "Service A", "Service B".
- **The relationships that matter** — what calls what, what is synchronous, where
  data is persisted, which path is the fast one.
- **The one thing a reader should walk away knowing.** If you cannot state this,
  the page probably does not need a figure here.
- **Placement and palette** — page width available, and the accent color, so the
  figure matches the site instead of arriving as a foreign object.

Ask for a horizontal figure when it sits in a content column; most page layouts
are far wider than they are tall, and a tall figure forces an awkward crop.

## When an icon is genuinely the right call

Diagrams are for mechanisms and relationships. Do not force one where there is
nothing to explain:

- **Navigation and UI affordances** — a hamburger, a search magnifier, a close X.
  These are interface controls, and icons are the correct vocabulary.
- **Dense lists** — a checkmark next to fourteen pricing-tier rows. A diagram per
  row would be absurd.
- **Brand and social links** — GitHub, npm, Discord marks.
- **Pure status** — a green dot for "operational".

The test: does the concept have *structure* — parts, ordering, flow, or state? If
yes, draw it. If it is a label or a control, use the icon. One excellent figure
beats six mediocre ones, so if a page supports three claims, three figures is
usually the right number, not one per section.

## Workflow

1. **Find the claims worth drawing.** Read the page and pick the two to four
   places where a reader would benefit from seeing the mechanism.
2. **Write a brief per figure** using the bullets above.
3. **Spawn a subagent per figure**, in parallel, telling each to read this skill.
4. **Compile with the bundled script** (the subagent does this):

   ```bash
   python3 scripts/tikz2svg.py figures/request-path.tex \
       -o figures/request-path.svg \
       --title "Request path through the edge cache" \
       --desc "A request hits the edge worker, which serves from cache or forwards to origin." \
       --map 2F6FEB=--fig-accent
   ```

   The script handles everything that makes raw `dvisvgm` output unsafe to inline:
   it rewrites black to `currentColor`, maps accent hexes to CSS custom
   properties, namespaces every internal id so multiple figures can share a page,
   drops absolute `pt` sizing in favor of the viewBox, and adds `role="img"` with
   `<title>`/`<desc>`. See `references/pipeline.md` for installation, flags, and
   troubleshooting.
5. **Look at the result.** Render the page and actually view it. Compiling
   without error only proves the TeX was valid, not that the arrows land where
   they should or that labels do not collide.
6. **Inline the SVG** into the page and commit the `.tex` alongside the `.svg`,
   so the figure stays editable rather than becoming a binary blob.

## Drawing figures that belong on a web page

The default TikZ look — hairline black strokes, Computer Modern serif, tight
academic spacing — reads as a paper scanned into a website. A few adjustments make
a figure look native. `references/recipes.md` has complete, compiling source for
the common archetypes (flow, layered architecture, sequence, state machine, tree,
comparison); start from the closest one rather than from a blank file.

- **Monochrome plus one accent.** Draw structure in the inherited text color and
  spend the accent on the single thing the figure is about — the fast path, the
  failure edge, the node under discussion. A figure where everything is colored
  emphasizes nothing.
- **Let the ink inherit.** Leave the default color alone in TikZ and the script
  converts it to `currentColor`, so the figure tracks light and dark mode without
  a second asset. Only name explicit colors for the accent.
- **Heavier strokes than TeX defaults.** `line width=0.6pt` on nodes and `0.7pt`
  on connectors survives being scaled down in a content column; hairlines vanish.
- **Set type once, at the top.** `font=\small\sffamily` on the picture, with
  `\scriptsize` for edge labels, gives a clear hierarchy. Sans-serif matches web
  body text; the bundled preamble already switches to it.
- **Breathe.** `node distance=16mm` and `inner sep=5pt` are better starting points
  than the TeX defaults, which are tuned for dense print figures.
- **Label the edges, not just the nodes.** "writes", "on miss", "async" is where
  the actual information lives — an unlabeled arrow only says two things are
  related, which the reader already assumed.
- **Aim for six to nine nodes.** Past that, split into two figures. A diagram that
  needs a legend to be read has usually failed.

## Putting the figure on the page

Inline the SVG directly rather than using `<img>`, so `currentColor` and the CSS
variables resolve against the page:

```html
<figure class="figure">
  <!-- contents of request-path.svg -->
  <figcaption>Requests are served at the edge; only misses reach origin.</figcaption>
</figure>
```

```css
.figure { color: var(--text); margin: 2.5rem auto; max-width: 46rem; }
.figure svg { width: 100%; height: auto; }
:root { --fig-accent: #2f6feb; }
@media (prefers-color-scheme: dark) {
  :root { --fig-accent: #74a3ff; }  /* lift the accent for contrast on dark */
}
```

Because the ink is `currentColor`, the figure recolors with its container and
needs no dark-mode variant. Do check the accent's contrast in dark mode — a hue
tuned for white backgrounds usually needs lightening.

## Verifying

A figure is done when:

- It renders legibly at the width it actually occupies, not just zoomed in.
- It reads correctly in both light and dark mode.
- Nothing overlaps and no arrow crosses through a node it does not touch.
- The `<title>`/`<desc>` convey the same point as the drawing, since that is what
  a screen-reader user gets.
- A reader who did not write the system could state the takeaway after ten
  seconds. If not, the figure is decoration with extra steps — the exact thing
  this skill exists to avoid.
