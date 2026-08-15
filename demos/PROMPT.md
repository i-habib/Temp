# The demo prompt

Both demo pages were built from the same base prompt. The only difference is a
single appended instruction. Everything else — the copy, the layout, the type,
the color palette — is held constant so the comparison isolates one variable:
**what the page uses to explain itself.**

## Base prompt (used by both)

> Build a single-page landing page for **Quanta**, an embedded time-series
> database that runs in-process, like SQLite for metrics.
>
> It should introduce the product and then explain how it actually works, in
> three sections:
>
> 1. **Ingest** — a write is appended to an on-disk write-ahead log for
>    durability and to an in-memory memtable so it is immediately queryable.
>    When the memtable reaches 4 MB it is flushed to an immutable block, which
>    truncates the WAL segment.
> 2. **Storage** — a block stores an 8-byte header, then timestamps
>    delta-of-delta encoded, then values XOR-encoded, then a footer holding the
>    min and max timestamp. Columns are stored separately, which compresses
>    about 11× better than row storage.
> 3. **Queries** — the planner reads each block's footer first and skips any
>    block whose min/max range does not overlap the query window, so a typical
>    query decodes only a couple of blocks out of hundreds.
>
> Single self-contained HTML file. Support light and dark mode. Make it look
> like a serious infrastructure product, not a startup template.

## The appended instruction

**`slop/index.html`** — nothing appended. This is the default output.

**`with-tikz/index.html`** — this paragraph appended:

> For anything technical on this page, do not use icons. An icon of a database
> or a lightning bolt does not explain anything — it decorates a claim the
> reader still has to take on faith. Instead, for each of the three mechanisms
> above, spawn a subagent that authors a real diagram in TikZ and compiles it to
> an inline SVG, following the `tikz-figure` skill. Each figure should draw the
> actual mechanism, using the real component names, with the one path that
> matters picked out in the accent color and the edges labeled. The figure has
> to make the claim legible to someone who did not already know how the system
> works. Keep icons only for navigation and links.

## What changed

| | `slop/` | `with-tikz/` |
|---|---|---|
| Explains ingest with | a lightning-bolt icon | a diagram of the write splitting to WAL and memtable |
| Explains storage with | a database icon | the actual byte layout of a block |
| Explains queries with | a magnifier icon | six blocks, four of them visibly skipped |
| Reader learns the mechanism | no | yes |
| Icons remaining | 3 decorative + nav | nav only |

The copy is *identical* in both files. Nothing was added to the prose to make the
second version more informative — the same sentences simply became legible
because there is now a picture of what they describe.
