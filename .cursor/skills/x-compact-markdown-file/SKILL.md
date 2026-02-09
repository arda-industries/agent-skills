---
name: x-compact-markdown-file
description: Normalize whitespace in a markdown file without changing semantic content (collapse excess blank lines, tighten lists).
---

When asked to "compact" a markdown file, perform a whitespace-normalization pass:

- Collapse **multiple empty lines** anywhere into **a single empty line**.
- For **lists** (bullets or numbered):
  - Remove empty blank lines **between list items**.
  - Remove empty blank lines **at the end of a list** (no trailing empty newline blocks after the final list item).

Do NOT change semantic content (no rewrapping paragraphs, no reordering list items, no changing indentation levels beyond what's required to remove empty lines).

