---
name: x-brain-workspace-orientation
description: Essential rules for operating in the ~/brain workspace. This is the primary guidance for all agents.
---

# Brain Workspace Rules

## Core principles

- **Brain is a container**: `~/brain` is not a single project. Each repo under `git/` has its own `.git`, dependencies, and workflows.
- **Project rules override**: When inside `git/personal/<project>/` or `git/work/<project>/`, that project's `.cursorrules`/`AGENTS.md`/`README.md` takes precedence.
- **Version control**: Agent instructions live in `git/personal/agent-instructions/` and must be git committed when modified.

## Directory structure

```
brain/
├── git/
│   ├── personal/           # Personal GitHub identity
│   │   ├── agent-instructions/  # THIS REPO - skills, tools, guidance
│   │   │   └── .cursor/skills/  # Canonical skill definitions
│   │   └── ...
│   └── work/               # Work GitHub identity
│       └── ...
├── obsidian/               # Obsidian knowledge vaults
│   ├── Timatron/           # Main vault (daily notes, GTD, journals)
│   └── ...
├── .cursorrules            # Thin pointer → this file
├── CLAUDE.md               # Thin pointer → this file
├── .cursor/skills/         # Symlink → agent-instructions/.cursor/skills/
└── .claude/skills/         # Symlink → agent-instructions/.cursor/skills/
```

## Skill discovery (symlinks)

Skills are defined canonically in `git/personal/agent-instructions/.cursor/skills/`. But Cursor and Claude Code discover skills from the **workspace root**, not from nested repos:

- **Cursor** looks for skills in `<workspace>/.cursor/skills/`
- **Claude Code** looks for skills in `<workspace>/.claude/skills/`

Since `~/brain` is the workspace root, the setup script (`setup.sh`) creates symlinks so both tools find the skills automatically:

```
~/brain/.cursor/skills  →  ~/brain/git/personal/agent-instructions/.cursor/skills
~/brain/.claude/skills  →  ~/brain/git/personal/agent-instructions/.cursor/skills
```

Both symlinks point to the **same source** — skills are authored once and discovered by both tools. If the symlinks break (e.g., after a fresh clone), re-run:

```bash
cd ~/brain/git/personal/agent-instructions
./setup.sh
```

## Git identities

- `git/personal/` — Personal GitHub identity (via SSH host alias `git@personal-github:...`)
- `git/work/` — Work GitHub identity (standard `git@github.com:...`; work key in `~/.ssh/config` for `Host github.com`)

**Avoid stray copies**: Only operate on repos under `git/personal/<repo>/` or `git/work/<repo>/`. If you see `git/<repo>/` directly without a `.git/` directory, it's a stray copy—find the canonical location.

## Obsidian safety

When editing files under `obsidian/`:
- Preserve `[[wikilinks]]` and existing markdown conventions
- Respect daily note formats in `daily/` and GTD files like `_DAILY.md`
- Keep diffs minimal; avoid unnecessary reformatting
- Journal files can be very large (e.g., 9MB)

## Agent tools

Skills and Python tools live in `git/personal/agent-instructions/`:

| Skill | Purpose |
|-------|---------|
| [Daily Briefing](../x-daily-briefing/SKILL.md) | Health briefing from TimTracker (sleep, exercise, diet, mindfulness) |
| [Update Daily Tasks](../x-update-daily-tasks/SKILL.md) | Refresh `_DAILY.md` from Asana |
| [Deep Research](../x-deep-research/SKILL.md) | Research using OpenAI's deep research API |
| [YouTube Analyzer](../x-youtube-analyzer/SKILL.md) | Analyze YouTube videos via Gemini API |
| [Product Deep Research](../x-product-deep-research/SKILL.md) | Combined web + video product research |
| [Convert PDF to Markdown](../x-convert-pdf-to-markdown/SKILL.md) | PDF conversion via PyMuPDF/marker-pdf |
| [Compact Markdown](../x-compact-markdown-file/SKILL.md) | Normalize whitespace |
| [TalkToFigma MCP](../x-talk-to-figma-mcp/SKILL.md) | Figma MCP server workflow |

**Python environment:**
```bash
cd ~/brain/git/personal/agent-instructions
poetry install
poetry run <command>
```

## Working with skills

When asked to do a known workflow, load the relevant skill `SKILL.md` and follow it exactly.

## Cursor cloud agents and nested work repos

When you open `~/brain` in Cursor, **cloud agents** (Cloud tab in the agent panel) are tied to a single Git repo. Brain has no repo at the root—repos live under `git/personal/` and `git/work/`. So from the brain workspace, cloud agents may not see a clear repo to clone (e.g. for `git/work/arda-intelligence/`).

**Options:**

1. **Default repo in Dashboard**  
   [Cursor Dashboard → Cloud Agents → Default repository](https://cursor.com/dashboard?tab=cloud-agents): set it to the work repo (e.g. `arda-industries/arda-intelligence`). When the workspace has no single repo, Cursor may then use this default when you start a cloud agent. Try this first.

2. **Multi-root workspace with work repo first**  
   Open a `.code-workspace` that lists the work repo as the **first** folder and brain (or a subfolder) as the second, so the “primary” repo for cloud agents is the work repo while you still have brain context. Create it once, then use **File → Open Workspace from File** and open that file.  
   Example (save as e.g. `~/brain/brain-arda.code-workspace`):
   ```json
   {
     "folders": [
       { "name": "arda-intelligence", "path": "git/work/arda-intelligence" },
       { "name": "brain", "path": "." }
     ],
     "settings": {}
   }
   ```
   Paths in `.code-workspace` are relative to the workspace file. So with the file in `~/brain`, `"path": "git/work/arda-intelligence"` is correct.

3. **Separate window when you need cloud agents**  
   If the above don’t reliably target the right repo: open **only** `~/brain/git/work/arda-intelligence` in a second Cursor window when you need to run cloud agents there. You lose the rest of brain in that window but cloud agents will work. This is the workaround many use on the Cursor forum.

**Note:** Parallel agents / worktrees and multi-repo cloud agents are limited today; Cursor is working on better multi-root and multi-repo support.

## Continuous improvement

If you hit issues or needed extra guidance, propose edits to the relevant instruction file, then `git commit` and `git push`.
