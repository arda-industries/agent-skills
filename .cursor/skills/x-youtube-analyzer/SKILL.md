---
name: x-youtube-analyzer
description: Analyze YouTube videos using Gemini's video understanding. Produces markdown reports with AI-generated summaries, key points, and extracted screenshots.
---

# YouTube Video Analyzer

Analyze YouTube videos with Gemini and extract screenshots at key moments.

## Agent Workflow

**IMPORTANT: Cursor agents must use `required_permissions: ["all"]` when running the shell command.** The default sandbox blocks network access, causing DNS errors like `[Errno 8] nodename nor servname provided, or not known`.

```bash
cd ~/brain/git/personal/agent-instructions
```

### Basic Usage

```bash
poetry run python scripts/youtube_analyzer.py analyze \
  "https://www.youtube.com/watch?v=VIDEO_ID" \
  --output ~/brain/obsidian/Timatron/Raw\ Transcripts\ \&\ Research/research/
```

### Multiple Videos

```bash
poetry run python scripts/youtube_analyzer.py analyze \
  "https://www.youtube.com/watch?v=VIDEO1" \
  "https://www.youtube.com/watch?v=VIDEO2" \
  --output ~/brain/obsidian/Timatron/Raw\ Transcripts\ \&\ Research/research/
```

### With Custom Title and Prompt

```bash
poetry run python scripts/youtube_analyzer.py analyze \
  "https://youtu.be/VIDEO_ID" \
  --title "AI Agent Architecture Review" \
  --prompt "Focus on the technical implementation details" \
  --output ~/brain/obsidian/Timatron/Raw\ Transcripts\ \&\ Research/research/
```

### Skip Screenshots (Analysis Only)

```bash
poetry run python scripts/youtube_analyzer.py analyze \
  "https://www.youtube.com/watch?v=VIDEO_ID" \
  --no-screenshots \
  --output ~/brain/obsidian/Timatron/Raw\ Transcripts\ \&\ Research/research/
```

## Prompt Templates

Use `--prompt` to focus the analysis. Here are useful patterns:

### Product Demo Analysis

For product walkthroughs, demos, or UI tours:

```bash
--prompt "Give me (1) a deep step-by-step analysis of the workflow steps, with as much detail as you can glean about what exactly the user is doing in the UI (what features they're using, what values they're entering, etc.). Link each step to the right timestamp. Then (2) produce a concise bullet point summary that (a) synthesizes what this product does (b) summarizes the features it has and (c) summarizes the workflow shown."
```

### Minute-by-Minute Summary

For talks, interviews, or educational content:

```bash
--prompt "Give me a bullet point list, one bullet per minute, with each bullet summarizing what was said in that minute. Group bullets under topic headings where natural. At the top add a concise 10 bullet point summary of the whole video."
```

## Options

| Option | Description |
|--------|-------------|
| `urls` | One or more YouTube URLs (positional, required) |
| `--output` | Output directory (default: current dir) |
| `--title` | Custom report title |
| `--prompt` | Additional analysis instructions |
| `--no-media` | Skip screenshot and clip extraction |
| `--max-screenshots` | Max screenshots per video (default: 5) |
| `--max-clips` | Max clips per video (default: 3) |
| `--model` | Gemini model (default: `gemini-2.5-flash`) |
| `--profile` | Google API profile name |

## Output

Creates a markdown file at `{output}/youtube-analysis-{date}.md` with:
- Video metadata (title, channel, URL, duration)
- AI-generated summary
- Key points with timestamps
- **Screenshots** for static content (diagrams, slides, code)
- **Animated clips** for dynamic content (demos, UI interactions, animations)

### Timestamp Formatting

**All timestamps MUST be clickable links to the YouTube video at that moment.**

Format: `**[MM:SS](https://www.youtube.com/watch?v=VIDEO_ID&t=XXs)**`

Where `XX` is the timestamp converted to seconds (e.g., `01:30` = 90s).

Example:
- ❌ `**[01:30]** - User opens the dashboard`
- ✅ `**[01:30](https://www.youtube.com/watch?v=abc123&t=90s)** — User opens the dashboard`

When consolidating YouTube analyses into reports, ensure ALL timestamps (in Key Points, Screenshots, Clips sections) are linked.

### Media Files

Saved to `~/brain/obsidian/Timatron/attachments/`:

| Type | Format | Naming | Purpose |
|------|--------|--------|---------|
| Screenshot | PNG | `yt-{video_id}-{MMmSSs}.png` | Static visuals |
| Clip (preview) | GIF | `yt-{video_id}-{MMmSSs}-{duration}s.gif` | Auto-plays in Obsidian |
| Clip (AI) | MP4 | `yt-{video_id}-{MMmSSs}-{duration}s.mp4` | High-quality for AI consumption |

Clips are extracted as both GIF (for Obsidian autoplay) and MP4 (for AI model consumption). GIFs are embedded in the report; MP4 paths are noted for reference.

## Usage Stats

After each run, the script displays detailed usage statistics:

```
==================================================
USAGE STATS
==================================================
  Model: gemini-2.5-flash
  Videos analyzed: 1
  Screenshots extracted: 5
  Clips extracted: 3 (GIF + MP4 each)

  Input tokens: 155,332
  Output tokens: 1,050
  Total tokens: 158,359

  Analysis time: 57.1s
  Media extraction time: 16.4s
  Total time: 73.9s

  Estimated cost: $0.0492
==================================================
```

**Pricing (per 1M tokens):**
| Model | Input | Output |
|-------|-------|--------|
| gemini-2.5-flash | $0.30 | $2.50 |
| gemini-2.5-pro | $2.50 | $15.00 |
| gemini-2.0-flash | $0.10 | $0.40 |

## API Key Setup

Edit `~/.config/google/profiles.json`:

```json
{
  "default": "personal",
  "profiles": {
    "personal": {
      "api_key": "AIza..."
    }
  }
}
```

Get an API key from: https://aistudio.google.com/apikey

## Requirements

- **ffmpeg**: Required for screenshot extraction (`brew install ffmpeg`)
- **yt-dlp**: Installed via poetry dependencies

## Limitations

- Only works with **public** YouTube videos (not private/unlisted)
- Free tier: 8 hours of YouTube video per day
- Videos longer than 1 hour use more tokens (~300 tokens/second)

## Troubleshooting

- **"[Errno 8] nodename nor servname provided"**: Cursor sandbox is blocking network access. Use `required_permissions: ["all"]` in the Shell tool call.
- **"ModuleNotFoundError: No module named 'google'"**: Run `poetry install` first to install dependencies.
- **"API key not found"**: Configure `~/.config/google/profiles.json`
- **"Video unavailable"**: Check if video is public and URL is correct
- **"ffmpeg not found"**: Install with `brew install ffmpeg`
- **No screenshots extracted**: Ensure ffmpeg is installed and video downloaded successfully
