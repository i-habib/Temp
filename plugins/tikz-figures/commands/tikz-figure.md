---
description: Add a real explanatory diagram to a technical page, replacing a decorative icon.
argument-hint: [what to diagram, e.g. "the request path on the landing page hero"]
---

Add one or more TikZ diagrams to this project, following the `tikz-figure` skill.

Target: $ARGUMENTS

Steps:

1. Read the `tikz-figure` skill for the design rules and workflow.
2. Identify the specific claims on the page that a diagram would support. If the
   target is vague, look at the page and propose two to four candidates before
   drawing anything.
3. For each figure, write a brief containing the claim it supports, the real
   component names, the relationships that matter, the single takeaway, and the
   page's accent color and available width.
4. Spawn one `tikz-figure-artist` subagent per figure, in parallel.
5. Inline the returned SVGs into the page, wire up the CSS variables, and check
   the result in both light and dark mode.

Report which icons or placeholders the diagrams replaced, and note any spot where
an icon was genuinely the right call and you left it alone.
