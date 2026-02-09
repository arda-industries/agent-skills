---
name: x-daily-briefing
description: Generate a daily briefing with health assessments (sleep, exercise, diet, mindfulness) from TimTracker data.
---

## Goal

Generate a daily briefing section in `obsidian/Timatron/GTD/_DAILY.md` that assesses the last week's health data from TimTracker:

- **Sleep**: Average hours, consistency, trends
- **Exercise**: Total minutes, workout types, frequency
- **Diet**: Average health score (1-10), trends
- **Mindfulness**: Total minutes, consistency

## Prerequisites

1. **TimTracker API key** must be configured at `~/.config/timtracker/config.json`:

```json
{
  "api_url": "https://timtracker-api.vercel.app",
  "api_key": "your-gpt-api-key-here"
}
```

The `api_key` is the `GPT_API_KEY` configured in Vercel for the TimTracker API.

## Step 1 — Fetch weekly health data

Run the Python script to fetch data and generate the briefing:

```bash
cd ~/brain/git/personal/agent-instructions
poetry run python scripts/daily_briefing.py
```

The script will:
1. Fetch the last 7 days of health data from `/api/weekly-summary`
2. Generate a markdown briefing with assessments for each category
3. Output the briefing to stdout

## Step 2 — Add briefing to daily document

Take the script output and add it to `obsidian/Timatron/GTD/_DAILY.md`:

1. Read the current contents of `_DAILY.md`
2. Find today's section (header `## YYYY-MM-DD`) or create one if it doesn't exist
3. Add a `### Health Briefing` subsection with the generated content
4. If a Health Briefing section already exists for today, replace it

### Section format

```markdown
## YYYY-MM-DD

### Health Briefing

#### Sleep
[Assessment of sleep quality, hours, consistency]

#### Exercise  
[Assessment of workout frequency, duration, types]

#### Diet
[Assessment of nutrition scores and trends]

#### Mindfulness
[Assessment of mindful minutes and consistency]

#### Summary
[Overall health assessment and recommendations]
```

## Goals and Targets (for assessment)

Use these targets when evaluating the data:

| Category | Target | Notes |
|----------|--------|-------|
| Sleep | 7-8 hours/night | Consistency matters more than occasional long sleeps |
| Exercise | 150+ min/week | Mix of cardio and strength preferred |
| Diet | Score 7+/10 | Higher scores indicate healthier eating |
| Mindfulness | 10+ min/day | Any amount is beneficial |

## Assessment Guidelines

When generating assessments:

1. **Be specific** — Use actual numbers from the data
2. **Note trends** — Is the metric improving, declining, or stable?
3. **Acknowledge gaps** — Missing data days are worth noting
4. **Be encouraging** — Frame feedback constructively
5. **Keep it brief** — 2-3 sentences per category max

## Troubleshooting

**API key not found**: Ensure `~/.config/timtracker/config.json` exists with valid credentials.

**No data returned**: Check that data exists in TimTracker for the date range. The API may return nulls for days without data.

**Authentication errors**: Verify the API key is correct and hasn't expired.
