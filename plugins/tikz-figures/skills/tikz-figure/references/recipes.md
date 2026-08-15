# Figure recipes

Working starting points for the archetypes that cover most technical pages. Each
one compiles as-is with `scripts/tikz2svg.py` — the bundled preamble supplies the
document class and libraries, so these files contain only the picture.

Copy the closest archetype and replace the content. Starting from a blank file
means rediscovering spacing and arrow styling every time.

| Archetype | Use it for |
|---|---|
| [Shared style block](#shared-style-block) | Put this at the top of any figure |
| [Linear flow](#1-linear-flow) | Request paths, build pipelines, ETL stages |
| [Layered architecture](#2-layered-architecture) | Stacks, tiers, subsystem grouping |
| [Sequence](#3-sequence) | Protocol handshakes, call ordering over time |
| [State machine](#4-state-machine) | Connection states, retry logic, lifecycles |
| [Tree](#5-tree) | Indexes, ASTs, routing tables, file layouts |
| [Byte layout](#6-byte-layout) | Packet headers, structs, on-disk formats |
| [Before / after](#7-before--after) | Migration arguments, optimization results |

---

## Shared style block

Every recipe below opens with this. It sets the type once, gives strokes enough
weight to survive being scaled into a content column, and defines one accent —
the color the script maps to a CSS variable.

```latex
\definecolor{accent}{HTML}{2F6FEB}
\begin{tikzpicture}[
  font=\small\sffamily,
  node distance=16mm,
  box/.style={draw, rounded corners=2pt, line width=.6pt,
              inner sep=5pt, minimum height=9mm, align=center},
  hl/.style={draw=accent, text=accent, line width=.8pt},
  flow/.style={-{Stealth[length=2mm,width=1.6mm]}, line width=.7pt},
  faint/.style={flow, dash pattern=on 2pt off 2pt},
  lbl/.style={font=\scriptsize\sffamily, inner sep=2pt},
]
```

Note what is *absent*: no explicit black. Leaving the default color alone is what
lets the script convert the ink to `currentColor` so the figure follows the
page's light/dark theme.

---

## 1. Linear flow

The workhorse. Reads left to right, with the accent carrying the one path that
matters and edge labels doing the explaining.

```latex
\definecolor{accent}{HTML}{2F6FEB}
\begin{tikzpicture}[
  font=\small\sffamily, node distance=15mm,
  box/.style={draw, rounded corners=2pt, line width=.6pt, inner sep=5pt,
              minimum height=9mm, minimum width=20mm, align=center},
  flow/.style={-{Stealth[length=2mm,width=1.6mm]}, line width=.7pt},
  lbl/.style={font=\scriptsize\sffamily, inner sep=2pt},
]
  \node[box] (client) {Client};
  \node[box, right=of client] (edge) {Edge\\worker};
  \node[box, right=of edge] (origin) {Origin};
  \node[box, below=11mm of origin] (db) {Postgres};

  \draw[flow] (client) -- node[lbl, above] {HTTPS} (edge);
  \draw[flow, draw=accent] (edge) -- node[lbl, above] {miss} (origin);
  \draw[flow] (origin) -- node[lbl, right] {query} (db);

  % The return path curves back so it never overlaps the forward arrow.
  \draw[flow, draw=accent] (edge.north) to[out=120, in=60, looseness=1.6]
        node[lbl, above] {hit: 12\,ms} (client.north);
\end{tikzpicture}
```

Two things worth stealing: the curved return edge (`to[out=..,in=..]`) keeps
bidirectional flows from stacking on one line, and the numeric label `12 ms`
turns a vague claim into evidence.

---

## 2. Layered architecture

`fit` draws a band around a group after its members are placed, so the band never
needs manual coordinates. `backgrounds` puts it behind the nodes.

```latex
\definecolor{accent}{HTML}{2F6FEB}
\begin{tikzpicture}[
  font=\small\sffamily,
  box/.style={draw, rounded corners=2pt, line width=.6pt, inner sep=5pt,
              minimum height=8mm, minimum width=24mm, align=center},
  band/.style={draw, rounded corners=3pt, line width=.5pt, dash pattern=on 2pt off 2pt,
               inner sep=4mm},
  lbl/.style={font=\scriptsize\sffamily},
]
  \node[box] (ui)   {Web UI};
  \node[box, right=6mm of ui] (cli) {CLI};

  \node[box, below=14mm of ui]  (api)  {REST API};
  \node[box, right=6mm of api]  (rpc)  {gRPC};

  \node[box, below=14mm of api] (store) {Storage engine};
  \node[box, right=6mm of store] (queue) {Job queue};

  \begin{scope}[on background layer]
    \node[band, fit=(ui)(cli),      label={[lbl]left:Clients}]  {};
    \node[band, fit=(api)(rpc),     label={[lbl]left:Services}] {};
    \node[band, fit=(store)(queue), label={[lbl]left:Data}]     {};
  \end{scope}

  \draw[-{Stealth[length=2mm]}, line width=.7pt] (ui)  -- (api);
  \draw[-{Stealth[length=2mm]}, line width=.7pt] (cli) -- (rpc);
  \draw[-{Stealth[length=2mm]}, line width=.7pt, draw=accent] (api) -- (store);
\end{tikzpicture}
```

---

## 3. Sequence

Time runs downward along dashed lifelines. Good for handshakes, where *ordering*
is the whole point and a box-and-arrow drawing would lose it.

```latex
\definecolor{accent}{HTML}{2F6FEB}
\begin{tikzpicture}[
  font=\small\sffamily,
  head/.style={draw, rounded corners=2pt, line width=.6pt, inner sep=4pt, minimum width=20mm},
  msg/.style={-{Stealth[length=2mm,width=1.6mm]}, line width=.7pt},
  lbl/.style={font=\scriptsize\sffamily, inner sep=2pt},
]
  \node[head] (c) at (0,0)    {Client};
  \node[head] (s) at (52mm,0) {Server};

  \draw[dash pattern=on 2pt off 2pt, line width=.4pt] (c) -- ++(0,-38mm);
  \draw[dash pattern=on 2pt off 2pt, line width=.4pt] (s) -- ++(0,-38mm);

  \draw[msg] ([yshift=-10mm]c.south) -- node[lbl, above] {ClientHello}     ([yshift=-10mm]s.south);
  \draw[msg] ([yshift=-18mm]s.south) -- node[lbl, above] {ServerHello, cert} ([yshift=-18mm]c.south);
  \draw[msg, draw=accent] ([yshift=-26mm]c.south) --
        node[lbl, above] {Finished} ([yshift=-26mm]s.south);
  \draw[msg, draw=accent] ([yshift=-34mm]s.south) --
        node[lbl, above] {application data} ([yshift=-34mm]c.south);
\end{tikzpicture}
```

Anchoring every message to `[yshift=-Nmm]` off the head keeps the vertical rhythm
even after you insert a step.

---

## 4. State machine

The `automata` library gives real state circles and self-loops.

```latex
\definecolor{accent}{HTML}{2F6FEB}
\begin{tikzpicture}[
  font=\small\sffamily, node distance=22mm, >={Stealth[length=2mm,width=1.6mm]},
  every state/.style={draw, line width=.6pt, inner sep=1pt, minimum size=13mm},
  lbl/.style={font=\scriptsize\sffamily},
]
  \node[state, initial, initial text={}] (idle)  {idle};
  \node[state, right=of idle]            (open)  {open};
  \node[state, right=of open, draw=accent, text=accent] (retry) {retry};

  \path[->, line width=.7pt]
    (idle)  edge node[lbl, above] {connect}  (open)
    (open)  edge node[lbl, above] {timeout}  (retry)
    (retry) edge[bend left=32] node[lbl, below] {backoff} (open)
    (open)  edge[loop above]    node[lbl] {heartbeat} ();
\end{tikzpicture}
```

---

## 5. Tree

Uses TikZ's built-in `child` syntax, which handles sibling spacing on its own.
The accent traces one lookup path — far more instructive than a bare structure.

```latex
\definecolor{accent}{HTML}{2F6FEB}
\begin{tikzpicture}[
  font=\small\sffamily,
  level 1/.style={sibling distance=34mm, level distance=15mm},
  level 2/.style={sibling distance=16mm, level distance=14mm},
  every node/.style={draw, rounded corners=2pt, line width=.6pt,
                     inner sep=4pt, minimum height=7mm},
  edge from parent/.style={draw, line width=.6pt, edge from parent path=
    {(\tikzparentnode.south) -- (\tikzchildnode.north)}},
  hot/.style={draw=accent, text=accent, line width=.8pt},
  lbl/.style={draw=none, font=\scriptsize\sffamily, inner sep=2pt},
]
  \node[hot] {50 | 90}
    child { node {12 | 30}
      child { node {4} }
      child { node {21} } }
    child { node[hot] {64 | 77}
      child { node {58} }
      child { node[hot] {71} } };

  % Annotate in the clear space beside the root rather than floating the label
  % somewhere in the middle of the tree, where it reads as a stray node.
  \node[lbl, anchor=west, text=accent] at (14mm, 4mm) {lookup 71};
\end{tikzpicture}
```

---

## 6. Byte layout

A row of fixed-width cells with a brace marking a span. Right for packet headers
and on-disk structs, where the sizes are the content.

```latex
\definecolor{accent}{HTML}{2F6FEB}
\begin{tikzpicture}[
  font=\small\sffamily, x=9mm, y=9mm,
  cell/.style={draw, line width=.6pt, minimum height=9mm, inner sep=2pt,
               font=\scriptsize\sffamily, align=center},
  lbl/.style={font=\scriptsize\sffamily},
]
  \foreach \i/\txt [count=\n from 0] in {0/magic, 1/ver, 2/flags, 3/len, 4/len, 5/crc, 6/crc, 7/crc} {
    \node[cell, minimum width=9mm] (b\n) at (\n, 0) {\txt};
  }
  \draw[decorate, decoration={brace, amplitude=4pt, raise=2pt}, line width=.5pt]
        (b3.north west) -- (b4.north east) node[lbl, midway, above=5pt] {payload length};
  % The index row sits between the cells and the lower brace, so the brace needs
  % a bigger `raise` to clear it — otherwise its label lands on the numbers.
  \node[lbl, anchor=east] at (-.6, 0) {byte};
  \foreach \n in {0,...,7} { \node[lbl] at (\n, -.72) {\n}; }

  \draw[decorate, decoration={brace, amplitude=4pt, raise=12pt, mirror}, line width=.5pt, draw=accent]
        (b5.south west) -- (b7.south east) node[lbl, midway, below=15pt, text=accent] {CRC-24};
\end{tikzpicture}
```

---

## 7. Before / after

Two small panels separated by a labeled arrow. The strongest figure for a
migration or optimization argument, because it shows the delta rather than
asserting it.

```latex
\definecolor{accent}{HTML}{2F6FEB}
\begin{tikzpicture}[
  font=\small\sffamily,
  box/.style={draw, rounded corners=2pt, line width=.6pt, inner sep=4pt,
              minimum width=17mm, minimum height=7mm, align=center},
  band/.style={draw, rounded corners=3pt, line width=.5pt,
               dash pattern=on 2pt off 2pt, inner sep=4mm},
  lbl/.style={font=\scriptsize\sffamily},
]
  % before: three sequential hops
  \node[box] (a1) at (0,0)      {app};
  \node[box] (a2) at (0,-11mm)  {adapter};
  \node[box] (a3) at (0,-22mm)  {db};
  \draw[-{Stealth[length=2mm]}, line width=.7pt] (a1) -- (a2);
  \draw[-{Stealth[length=2mm]}, line width=.7pt] (a2) -- (a3);

  % after: one hop
  \node[box] (b1) at (52mm,-5.5mm)  {app};
  \node[box, draw=accent, text=accent] (b2) at (52mm,-16.5mm) {db};
  \draw[-{Stealth[length=2mm]}, line width=.7pt, draw=accent] (b1) -- (b2);

  \begin{scope}[on background layer]
    \node[band, fit=(a1)(a3), label={[lbl]above:before: 3 hops, 40\,ms}] {};
    \node[band, fit=(b1)(b2), label={[lbl]above:after: 1 hop, 9\,ms}] {};
  \end{scope}

  \draw[-{Stealth[length=2.4mm,width=2mm]}, line width=.9pt, draw=accent]
        (20mm,-11mm) -- node[lbl, above, text=accent] {drop the adapter} (32mm,-11mm);
\end{tikzpicture}
```

---

## Positioning cheatsheet

| Goal | Syntax |
|---|---|
| Place relative to another node | `right=of a`, `below=14mm of a` |
| Nudge an anchor | `([yshift=-4mm]a.south)` |
| Curve around an obstacle | `to[out=120, in=60] (b)` |
| Bend a straight edge | `edge[bend left=30]` |
| Group after placement | `node[fit=(a)(b)(c)]` inside `on background layer` |
| Repeat a shape | `\foreach \i in {0,...,7}` |
| Midpoint of an edge | `node[midway, above] {label}` |
| Multi-line node text | `align=center` plus `\\` |

## Common failures

- **Arrow starts inside a node.** Draw between node *names* (`(a) -- (b)`), not
  coordinates; TikZ then clips to the borders automatically.
- **Labels collide at small sizes.** Raise `node distance` before shrinking type —
  crowding is nearly always a spacing problem, not a font-size one.
- **The figure is taller than it is wide.** Rotate the flow to horizontal, or
  split it. Content columns are wide and short.
- **Everything is accent-colored.** Cut back to one highlighted path. Emphasis
  requires something unemphasized to contrast against.
- **`fit` band lands in the wrong place.** It must come after the nodes it fits,
  inside `\begin{scope}[on background layer]`.
