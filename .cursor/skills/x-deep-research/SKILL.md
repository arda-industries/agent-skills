---
name: x-deep-research
description: Conduct deep research using OpenAI's deep research models via API. Use when the user asks for comprehensive analysis, company research, person research, or product research requiring web-sourced citations.
---

# Deep Research

Conduct citation-backed research using OpenAI's deep research models.

## Agent Workflow

```bash
cd ~/brain/git/personal/agent-instructions
```

**0. Ask model** → **1. Submit** → **2. Poll status** → **3. Download** → **4. Post-process**

### 0. Ask User: Model Selection (REQUIRED)

Before submitting, ask the user which model to use:

| Model | Quality | Cost | Use When |
|-------|---------|------|----------|
| **o3-deep-research** | Higher | $1-3 | Important research, external-facing, deep analysis |
| **o4-mini-deep-research** | Good | $0.20-0.60 | Quick lookups, internal use, cost-sensitive |

Present this choice and wait for user response before proceeding.

### 1. Submit

```bash
poetry run python scripts/deep_research.py submit \
  --template company \
  --topic "Company Name" \
  --model o3-deep-research \
  --output ~/brain/obsidian/Timatron/Raw\ Transcripts\ \&\ Research/research/
```

Templates: `company`, `person`, `product`, `custom` (use `--query` for custom)
Models: `o3-deep-research` (default), `o4-mini-deep-research`

### 2. Poll Status

```bash
poetry run python scripts/deep_research.py status <response_id>
```

Research takes 5-30 minutes. Poll every few minutes until `completed`.

### 3. Download

```bash
poetry run python scripts/deep_research.py download <response_id> \
  --output ~/brain/obsidian/Timatron/Raw\ Transcripts\ \&\ Research/research/
```

**Report usage stats to user** (shown after download):
- Model, duration, token counts, cost

### 4. Post-Process Citations (REQUIRED)

After downloading, edit the report to convert parenthetical citations to inline links:

**Before:** `The company raised $100M ([source.com](url)).`
**After:** `The company [raised $100M](url).`

Also consolidate duplicate citations — one link per fact is sufficient.

## API Key Setup

Edit `~/.config/openai/profiles.json`:

```json
{
  "default": "personal",
  "profiles": {
    "personal": {
      "api_key": "sk-proj-YOUR-KEY-HERE"
    }
  }
}
```

Use `--profile <name>` to select a profile. Falls back to `OPENAI_API_KEY` env var.

## Pricing Reference

| Model | Input/M tokens | Output/M tokens |
|-------|----------------|-----------------|
| o3-deep-research | $10.00 | $40.00 |
| o4-mini-deep-research | $2.00 | $8.00 |

Typical query uses 50-100K tokens. Exact cost reported after download.

## Prompt Templates

Located in `prompts/`:
- `base.md` — Common instructions (word limits, citation style, format rules)
- `company.md` — Company research structure
- `person.md` — Person research structure  
- `product.md` — Product research structure

## Troubleshooting

- **"API key not found"**: Configure profiles.json or set `OPENAI_API_KEY`
- **"model_not_found"**: Verify org at https://platform.openai.com/settings/organization/general
- **"insufficient_quota"**: Add credits at https://platform.openai.com/settings/organization/billing
