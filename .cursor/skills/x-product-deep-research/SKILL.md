---
name: x-product-deep-research
description: Comprehensive product research combining OpenAI deep research (web) with Gemini YouTube analysis (video). Use for thorough product evaluation with demos, interviews, and visual documentation.
---

# Product Deep Research

Combines deep web research with YouTube video analysis for comprehensive product intelligence.

**Cost estimate:** $0.50-3.00 total (deep research + video analysis)
**Time estimate:** 15-40 minutes (mostly waiting for deep research)

## When to Use

- Evaluating a product for purchase/adoption
- Competitive analysis requiring visual demos
- Understanding a product's actual UX (not just marketing)
- Researching products with significant video content (SaaS, hardware, tools)

## Agent Workflow

```bash
cd ~/brain/git/personal/agent-instructions
```

### Phase 1: Deep Research (OpenAI)

**1.1 Ask user for model choice:**

| Model | Quality | Cost | Use When |
|-------|---------|------|----------|
| **o3-deep-research** | Higher | $1-3 | Important decisions, external-facing |
| **o4-mini-deep-research** | Good | $0.20-0.60 | Quick evaluation, internal use |

**1.2 Submit deep research:**

```bash
poetry run python scripts/deep_research.py submit \
  --template product \
  --topic "BuildOS by Dirac" \
  --model o3-deep-research \
  --output ~/brain/obsidian/Timatron/Raw\ Transcripts\ \&\ Research/research/
```

**1.3 Poll until complete:**

```bash
poetry run python scripts/deep_research.py status <response_id>
```

Research takes 10-30 minutes. Poll every few minutes.

**1.4 Download results:**

```bash
poetry run python scripts/deep_research.py download <response_id> \
  --output ~/brain/obsidian/Timatron/Raw\ Transcripts\ \&\ Research/research/
```

### Phase 2: Extract and Filter YouTube URLs

**2.1 Read the deep research report and find the "Video Resources" section.**

Extract all YouTube URLs from the report. Look for:
- `https://www.youtube.com/watch?v=...`
- `https://youtu.be/...`

**2.2 Filter videos for substance over marketing.**

Prioritize videos that show **actual product usage with feature detail**. The goal is to understand real workflows and UX, not marketing messaging.

**HIGH VALUE (analyze these):**
- Hands-on demos walking through specific workflows step-by-step
- Tutorial videos showing how to accomplish real tasks
- User/customer walkthroughs of their actual usage
- Conference talks with live product demonstrations
- Third-party reviews with screen recordings of the product
- Videos 5+ minutes that spend most time showing the actual UI

**LOW VALUE (skip or deprioritize):**
- Marketing videos with mostly animations, graphics, or talking heads
- Videos that show UI only briefly (<30 sec of actual product)
- Hype/announcement videos focused on messaging over features
- Videos under 2 minutes (rarely have enough substance)
- Webinar recordings that are mostly slides, not product
- Testimonials where customers talk about benefits without showing the product

**Signals of a good demo:**
- Title includes: "tutorial", "walkthrough", "how to", "demo", "getting started"
- Longer duration (10-30 min usually means depth)
- Published by power users, consultants, or training channels
- Shows cursor moving through actual UI for extended periods

**Signals of marketing fluff:**
- Title includes: "introducing", "announcement", "why", "vision", "future"
- Slick motion graphics and transitions
- Multiple camera angles on speakers with brief UI cuts
- Focuses on "what" and "why" rather than "how"

**2.3 Present filtered videos to user for confirmation:**

```
Found {N} YouTube videos about {product}.

RECOMMENDED FOR ANALYSIS ({M} videos):
These show substantial product demos with workflow detail.

1. ⭐ {Title} ({Duration}) - {Type}
   {URL}
   Why: {Brief reason - e.g., "20-min hands-on tutorial covering core workflow"}
   
2. ⭐ {Title} ({Duration}) - {Type}
   {URL}
   Why: {Brief reason}

SKIPPING ({K} videos):
These appear to be marketing/overview content without detailed demos.

3. ⏭️ {Title} ({Duration}) - {Type}
   {URL}
   Why skipped: {e.g., "2-min announcement video, mostly animations"}

Estimated YouTube analysis cost: ~${cost} ({total_minutes} min of video)

Proceed with recommended videos? Or adjust the selection.
```

Wait for user confirmation before proceeding.

### Phase 3: YouTube Analysis (Gemini)

**3.1 Run YouTube analyzer on confirmed videos:**

```bash
PYTHONUNBUFFERED=1 poetry run python scripts/youtube_analyzer.py analyze \
  "https://www.youtube.com/watch?v=VIDEO1" \
  "https://www.youtube.com/watch?v=VIDEO2" \
  "https://www.youtube.com/watch?v=VIDEO3" \
  --title "BuildOS Video Analysis" \
  --output ~/brain/obsidian/Timatron/Raw\ Transcripts\ \&\ Research/research/
```

**IMPORTANT: Always include media extraction (screenshots/clips).**

- Do NOT use `--no-media` flag unless the user explicitly requests it
- `PYTHONUNBUFFERED=1` ensures you see progress output in real-time
- Media extraction requires downloading videos locally, which can be slow

This extracts:
- Summaries and key points
- Screenshots (static moments)
- GIF/MP4 clips (dynamic moments)

**3.2 Handle download failures:**

If video downloads fail or timeout:

1. **Do NOT silently skip media extraction**
2. **Pause and inform the user:**

```
⚠️ Video download failed for {N} video(s):
- {video_title}: {error reason, e.g., "Download timed out after 10 minutes"}

Options:
A) Retry downloads (may take longer on slow network)
B) Skip media extraction for failed videos (keep text analysis)
C) Pause and retry later when network is better

What would you like to do?
```

3. Wait for user response before proceeding
4. If user chooses to skip, note it clearly in the final report:
   - "Screenshots: 0 (downloads failed, user chose to skip)"

### Phase 4: Combine Reports

**4.1 Create unified report:**

Create a new file: `{product}-deep-research-{date}.md`

Use this structure:

```markdown
---
title: "Product Deep Research: {Product} by {Company}"
date: {YYYY-MM-DD}
type: product-deep-research
---

# {Product} by {Company}

## Executive Summary
[Copy from deep research report]

## Product Deep Dive
[Copy from deep research report]

---

## Video Demonstrations

> Analysis based on {N} YouTube videos totaling {X} minutes of content.

[For each video from YouTube analysis, include:]

### {Video Title}

**URL:** {url}
**Channel:** {channel}
**Type:** Demo / Interview / Tutorial / Review

#### Summary
[From YouTube analysis]

#### Key Points
[From YouTube analysis - bulleted list with LINKED timestamps]
- Format timestamps as: `**[MM:SS](https://www.youtube.com/watch?v=VIDEO_ID&t=XXs)**`
- Example: `**[01:30](https://www.youtube.com/watch?v=abc123&t=90s)** — User opens dashboard`

#### Visual Highlights

[Include 2-3 most relevant screenshots/clips]

**[{timestamp}](https://www.youtube.com/watch?v=VIDEO_ID&t=XXs)** — {description}
![[{screenshot_or_gif_filename}]]

---

## Pricing & Packaging
[Copy from deep research report]

## Competitive Landscape
[Copy from deep research report]

## User Reception
[Copy from deep research report]

## Recommendations
[Copy from deep research report]

---

## Sources

### Web Sources
[Copy sources section from deep research report]

### Video Sources
1. [{Video 1 Title}]({url})
2. [{Video 2 Title}]({url})
...
```

**4.2 Post-process:**

- Convert parenthetical citations to inline links (as per deep research skill)
- Ensure all screenshots/clips are properly embedded
- Remove any duplicate information between sections

**4.3 Report to user:**

```
Product deep research complete!

Report: ~/brain/obsidian/Timatron/Raw\ Transcripts\ \&\ Research/research/{product}-deep-research-{date}.md

Stats:
- Web sources: {N}
- Videos analyzed: {N}
- Screenshots extracted: {N}
- Clips extracted: {N}

Total cost: ~${deep_research_cost + youtube_cost}
```

## Example Invocation

User: "Do deep product research on BuildOS by Dirac"

Agent:
1. Asks about model choice (o3 vs o4-mini)
2. Submits deep research, polls until complete
3. Extracts YouTube URLs from report
4. Presents videos for confirmation
5. Runs YouTube analysis
6. Combines into unified report
7. Reports completion with stats

## Cost Breakdown

| Phase | Model | Typical Cost |
|-------|-------|--------------|
| Deep Research | o3-deep-research | $1.00-2.50 |
| Deep Research | o4-mini-deep-research | $0.20-0.50 |
| YouTube Analysis | gemini-2.5-flash | $0.03-0.05/min video |

Example: 4 videos @ 5 min each = 20 min = ~$0.80 for YouTube analysis
