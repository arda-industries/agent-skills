# Agent Instructions

Versioned agent guidance, skills, and Python tools for the `brain` workspace.

## Quick start (new machine)

```bash
# 1. Clone this repo
git clone git@github.com:youruser/agent-instructions.git

# 2. Run setup (creates ~/brain structure + pointer files)
cd agent-instructions
./setup.sh
```

## Skills

Skills live in `.cursor/skills/`. Each folder contains a `SKILL.md`.

The primary guidance is **[Brain Workspace Orientation](.cursor/skills/x-brain-workspace-orientation/SKILL.md)** — this is what `.cursorrules` and `CLAUDE.md` point to.

Other skills:

| Skill | Purpose |
|-------|---------|
| [Daily Briefing](.cursor/skills/x-daily-briefing/SKILL.md) | Health briefing from TimTracker (sleep, exercise, diet, mindfulness) |
| [Update Daily Tasks](.cursor/skills/x-update-daily-tasks/SKILL.md) | Refresh `_DAILY.md` from Asana |
| [Deep Research](.cursor/skills/x-deep-research/SKILL.md) | Research using OpenAI's deep research API |
| [YouTube Analyzer](.cursor/skills/x-youtube-analyzer/SKILL.md) | Analyze YouTube videos via Gemini API |
| [Product Deep Research](.cursor/skills/x-product-deep-research/SKILL.md) | Combined web + video product research |
| [Convert PDF to Markdown](.cursor/skills/x-convert-pdf-to-markdown/SKILL.md) | PDF conversion via PyMuPDF/marker-pdf |
| [Compact Markdown](.cursor/skills/x-compact-markdown-file/SKILL.md) | Normalize whitespace |
| [TalkToFigma MCP](.cursor/skills/x-talk-to-figma-mcp/SKILL.md) | Figma MCP server workflow |

## Python environment

```bash
cd ~/brain/git/personal/agent-instructions
poetry install
poetry run <command>
```

**Installed packages:** `openai`, `google-genai`, `yt-dlp`, `pymupdf`, `marker-pdf`

## Version control

All agent instructions must be git versioned. After modifying guidance, commit and push.
