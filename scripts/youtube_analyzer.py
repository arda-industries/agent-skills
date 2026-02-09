#!/usr/bin/env python3
"""
YouTube Video Analyzer

Analyze YouTube videos using Google's Gemini API and extract screenshots
at key moments using yt-dlp and ffmpeg.

Usage:
    poetry run python scripts/youtube_analyzer.py analyze "https://youtube.com/watch?v=VIDEO_ID"
    poetry run python scripts/youtube_analyzer.py analyze URL1 URL2 --output ~/research/
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Pricing per million tokens (as of Jan 2026)
# https://ai.google.dev/gemini-api/docs/pricing
MODEL_PRICING = {
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
    "gemini-2.5-pro": {"input": 2.50, "output": 15.00},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
}

# Directory containing this script
SCRIPT_DIR = Path(__file__).parent.resolve()
# Skills directory with prompts
SKILLS_DIR = SCRIPT_DIR.parent / ".cursor" / "skills" / "x-youtube-analyzer"
PROMPTS_DIR = SKILLS_DIR / "prompts"
# Config file for profiles
PROFILES_PATH = Path.home() / ".config" / "google" / "profiles.json"
# Default attachments directory for Obsidian
DEFAULT_ATTACHMENTS_DIR = Path.home() / "brain" / "obsidian" / "Timatron" / "attachments"


def get_api_key(profile: Optional[str] = None) -> str:
    """Get Google API key from profiles.json config file."""
    if PROFILES_PATH.exists():
        with open(PROFILES_PATH) as f:
            config = json.load(f)
        
        profiles = config.get("profiles", {})
        
        # If explicit profile specified, use it
        if profile:
            if profile not in profiles:
                available = ", ".join(profiles.keys())
                print(f"Error: Profile '{profile}' not found. Available: {available}")
                sys.exit(1)
            
            api_key = profiles[profile].get("api_key")
            if not api_key or api_key.startswith("YOUR_"):
                print(f"Error: API key for profile '{profile}' is not configured.")
                print(f"Edit {PROFILES_PATH} and add your API key.")
                sys.exit(1)
            
            return api_key
        
        # Use default profile
        default_profile = config.get("default")
        if default_profile and default_profile in profiles:
            api_key = profiles[default_profile].get("api_key")
            if api_key and not api_key.startswith("YOUR_"):
                return api_key
            else:
                print(f"Error: API key for default profile '{default_profile}' is not configured.")
                print(f"Edit {PROFILES_PATH} and replace the placeholder with your API key.")
                sys.exit(1)
    
    # Fall back to environment variable
    api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key:
        return api_key
    
    print("Error: No API key found.")
    print()
    print("Option 1: Configure profiles.json (recommended)")
    print(f"  Edit: {PROFILES_PATH}")
    print()
    print("Option 2: Set environment variable")
    print("  export GOOGLE_API_KEY='AIza...'")
    sys.exit(1)


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
        r'(?:shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def parse_timestamp(ts: str) -> Optional[int]:
    """Parse MM:SS or HH:MM:SS timestamp to seconds."""
    ts = ts.strip()
    parts = ts.split(':')
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        pass
    return None


def format_timestamp_filename(seconds: int) -> str:
    """Format seconds as MMmSSs for filename."""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}m{secs:02d}s"


def format_duration(seconds: int) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"


@dataclass
class StaticMoment:
    """A moment best captured as a screenshot (diagrams, slides, code)."""
    timestamp_str: str
    timestamp_seconds: int
    description: str
    screenshot_path: Optional[Path] = None


@dataclass
class DynamicMoment:
    """A moment best captured as a short clip (demos, animations, interactions)."""
    timestamp_str: str
    timestamp_seconds: int
    duration_seconds: int  # How long the clip should be (1-5s)
    description: str
    gif_path: Optional[Path] = None
    mp4_path: Optional[Path] = None


@dataclass
class UsageStats:
    """Track API usage and timing for a single analysis."""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    analysis_time_seconds: float = 0.0
    media_extraction_time_seconds: float = 0.0
    
    @property
    def cost_usd(self) -> float:
        """Calculate cost based on model pricing."""
        pricing = MODEL_PRICING.get(self.model, MODEL_PRICING["gemini-2.5-flash"])
        input_cost = (self.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost


@dataclass
class VideoAnalysis:
    url: str
    video_id: str
    title: str = ""
    channel: str = ""
    duration_seconds: int = 0
    summary: str = ""
    key_points: list[tuple[str, str]] = field(default_factory=list)  # (timestamp, point)
    static_moments: list[StaticMoment] = field(default_factory=list)
    dynamic_moments: list[DynamicMoment] = field(default_factory=list)
    raw_response: str = ""
    usage: UsageStats = field(default_factory=UsageStats)


def parse_gemini_response(response_text: str, video_id: str) -> VideoAnalysis:
    """Parse the structured response from Gemini."""
    analysis = VideoAnalysis(url="", video_id=video_id)
    analysis.raw_response = response_text
    
    # Extract TITLE
    title_match = re.search(r'TITLE:\s*(.+?)(?:\n|$)', response_text)
    if title_match:
        analysis.title = title_match.group(1).strip()
    
    # Extract CHANNEL
    channel_match = re.search(r'CHANNEL:\s*(.+?)(?:\n|$)', response_text)
    if channel_match:
        analysis.channel = channel_match.group(1).strip()
    
    # Extract SUMMARY
    summary_match = re.search(r'SUMMARY:\s*\n(.*?)(?=\nKEY_POINTS:|$)', response_text, re.DOTALL)
    if summary_match:
        analysis.summary = summary_match.group(1).strip()
    
    # Extract KEY_POINTS
    key_points_match = re.search(r'KEY_POINTS:\s*\n(.*?)(?=\nSTATIC_MOMENTS:|VISUAL_MOMENTS:|$)', response_text, re.DOTALL)
    if key_points_match:
        points_text = key_points_match.group(1)
        for line in points_text.strip().split('\n'):
            line = line.strip()
            if line.startswith('-'):
                line = line[1:].strip()
            # Match [MM:SS] or [HH:MM:SS] followed by text
            point_match = re.match(r'\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*[-–—]?\s*(.+)', line)
            if point_match:
                analysis.key_points.append((point_match.group(1), point_match.group(2)))
    
    # Extract STATIC_MOMENTS (screenshots)
    static_match = re.search(r'STATIC_MOMENTS:\s*\n(.*?)(?=\nDYNAMIC_MOMENTS:|$)', response_text, re.DOTALL)
    if static_match:
        static_text = static_match.group(1)
        for line in static_text.strip().split('\n'):
            line = line.strip()
            if line.startswith('-'):
                line = line[1:].strip()
            # Match [MM:SS] followed by description
            moment_match = re.match(r'\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*[-–—]?\s*(.+)', line)
            if moment_match:
                ts_str = moment_match.group(1)
                ts_seconds = parse_timestamp(ts_str)
                if ts_seconds is not None:
                    analysis.static_moments.append(StaticMoment(
                        timestamp_str=ts_str,
                        timestamp_seconds=ts_seconds,
                        description=moment_match.group(2)
                    ))
    
    # Extract DYNAMIC_MOMENTS (clips)
    dynamic_match = re.search(r'DYNAMIC_MOMENTS:\s*\n(.*?)(?=\n---|$)', response_text, re.DOTALL)
    if dynamic_match:
        dynamic_text = dynamic_match.group(1)
        for line in dynamic_text.strip().split('\n'):
            line = line.strip()
            if line.startswith('-'):
                line = line[1:].strip()
            # Match [MM:SS] (Xs) followed by description
            # e.g., [02:30] (3s) UI demonstration of drag-and-drop
            moment_match = re.match(
                r'\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*\((\d+)s?\)?\s*[-–—]?\s*(.+)', 
                line
            )
            if moment_match:
                ts_str = moment_match.group(1)
                ts_seconds = parse_timestamp(ts_str)
                duration = int(moment_match.group(2))
                # Clamp duration to 1-5 seconds
                duration = max(1, min(5, duration))
                if ts_seconds is not None:
                    analysis.dynamic_moments.append(DynamicMoment(
                        timestamp_str=ts_str,
                        timestamp_seconds=ts_seconds,
                        duration_seconds=duration,
                        description=moment_match.group(3)
                    ))
    
    # Fallback: if old VISUAL_MOMENTS format is used, treat as static
    if not analysis.static_moments and not analysis.dynamic_moments:
        visual_match = re.search(r'VISUAL_MOMENTS:\s*\n(.*?)(?=\n---|$)', response_text, re.DOTALL)
        if visual_match:
            visual_text = visual_match.group(1)
            for line in visual_text.strip().split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    line = line[1:].strip()
                moment_match = re.match(r'\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*[-–—]?\s*(.+)', line)
                if moment_match:
                    ts_str = moment_match.group(1)
                    ts_seconds = parse_timestamp(ts_str)
                    if ts_seconds is not None:
                        analysis.static_moments.append(StaticMoment(
                            timestamp_str=ts_str,
                            timestamp_seconds=ts_seconds,
                            description=moment_match.group(2)
                        ))
    
    return analysis


def analyze_video_with_gemini(
    url: str,
    model: str,
    api_key: str,
    custom_prompt: Optional[str] = None
) -> VideoAnalysis:
    """Analyze a YouTube video using Gemini's video understanding."""
    from google import genai
    from google.genai import types
    
    video_id = extract_video_id(url)
    if not video_id:
        print(f"  Error: Could not extract video ID from URL: {url}")
        return VideoAnalysis(url=url, video_id="unknown")
    
    # Load the default analysis prompt
    prompt_path = PROMPTS_DIR / "analyze.md"
    if prompt_path.exists():
        base_prompt = prompt_path.read_text()
    else:
        base_prompt = "Analyze this YouTube video and provide a summary with key points and timestamps."
    
    # Append custom prompt if provided
    if custom_prompt:
        base_prompt += f"\n\n## Additional Instructions\n{custom_prompt}"
    
    print(f"  Sending to Gemini ({model})...")
    
    client = genai.Client(api_key=api_key)
    
    try:
        start_time = time.time()
        
        response = client.models.generate_content(
            model=model,
            contents=types.Content(parts=[
                types.Part(file_data=types.FileData(file_uri=url)),
                types.Part(text=base_prompt)
            ])
        )
        
        analysis_time = time.time() - start_time
        
        response_text = response.text
        analysis = parse_gemini_response(response_text, video_id)
        analysis.url = url
        
        # Extract usage stats
        usage = UsageStats(model=model, analysis_time_seconds=analysis_time)
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            um = response.usage_metadata
            usage.input_tokens = getattr(um, 'prompt_token_count', 0) or 0
            usage.output_tokens = getattr(um, 'candidates_token_count', 0) or 0
            usage.total_tokens = getattr(um, 'total_token_count', 0) or usage.input_tokens + usage.output_tokens
        analysis.usage = usage
        
        print(f"  Analysis complete: {analysis.title or 'Untitled'}")
        print(f"  Key points: {len(analysis.key_points)}, Static: {len(analysis.static_moments)}, Dynamic: {len(analysis.dynamic_moments)}")
        print(f"  Tokens: {usage.input_tokens:,} in / {usage.output_tokens:,} out | Cost: ${usage.cost_usd:.4f} | Time: {analysis_time:.1f}s")
        
        return analysis
        
    except Exception as e:
        print(f"  Error analyzing video: {e}")
        return VideoAnalysis(url=url, video_id=video_id)


def download_video(url: str, output_dir: Path) -> Optional[Path]:
    """Download video using yt-dlp."""
    video_id = extract_video_id(url)
    if not video_id:
        return None
    
    output_path = output_dir / f"{video_id}.mp4"
    
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o", str(output_path),
        "--no-playlist",
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0 and output_path.exists():
            return output_path
        else:
            print(f"  yt-dlp error: {result.stderr[:200] if result.stderr else 'Unknown error'}")
            return None
    except subprocess.TimeoutExpired:
        print(f"  Download timed out after 10 minutes")
        return None
    except Exception as e:
        print(f"  Download error: {e}")
        return None


def extract_frame(video_path: Path, timestamp_seconds: int, output_path: Path) -> bool:
    """Extract a single frame from video at the given timestamp using ffmpeg."""
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-ss", str(timestamp_seconds),  # Seek to timestamp
        "-i", str(video_path),  # Input file
        "-frames:v", "1",  # Extract 1 frame
        "-q:v", "2",  # High quality
        str(output_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0 and output_path.exists()
    except Exception as e:
        print(f"    ffmpeg error: {e}")
        return False


def extract_clip_gif(
    video_path: Path, 
    timestamp_seconds: int, 
    duration_seconds: int,
    output_path: Path,
    width: int = 480
) -> bool:
    """Extract a short GIF clip from video using ffmpeg."""
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-ss", str(timestamp_seconds),  # Seek to timestamp
        "-t", str(duration_seconds),  # Duration
        "-i", str(video_path),  # Input file
        "-vf", f"fps=10,scale={width}:-1:flags=lanczos",  # 10fps, scale width
        "-loop", "0",  # Loop forever
        str(output_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0 and output_path.exists()
    except Exception as e:
        print(f"    ffmpeg GIF error: {e}")
        return False


def extract_clip_mp4(
    video_path: Path, 
    timestamp_seconds: int, 
    duration_seconds: int,
    output_path: Path
) -> bool:
    """Extract a short MP4 clip from video using ffmpeg."""
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-ss", str(timestamp_seconds),  # Seek to timestamp
        "-t", str(duration_seconds),  # Duration
        "-i", str(video_path),  # Input file
        "-c:v", "libx264",  # H.264 codec
        "-preset", "fast",  # Fast encoding
        "-crf", "23",  # Quality (lower = better, 23 is default)
        "-an",  # No audio
        str(output_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0 and output_path.exists()
    except Exception as e:
        print(f"    ffmpeg MP4 error: {e}")
        return False


def extract_media(
    analysis: VideoAnalysis,
    attachments_dir: Path,
    max_screenshots: int = 5,
    max_clips: int = 3
) -> None:
    """Download video and extract screenshots and clips at identified moments."""
    has_static = bool(analysis.static_moments)
    has_dynamic = bool(analysis.dynamic_moments)
    
    if not has_static and not has_dynamic:
        print(f"  No moments to extract")
        return
    
    # Limit extractions
    static_to_extract = analysis.static_moments[:max_screenshots]
    dynamic_to_extract = analysis.dynamic_moments[:max_clips]
    
    print(f"  Downloading video for media extraction...")
    
    start_time = time.time()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        video_path = download_video(analysis.url, temp_path)
        
        if not video_path:
            print(f"  Could not download video, skipping media extraction")
            return
        
        attachments_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract screenshots for static moments
        if static_to_extract:
            print(f"  Extracting {len(static_to_extract)} screenshots...")
            for moment in static_to_extract:
                filename = f"yt-{analysis.video_id}-{format_timestamp_filename(moment.timestamp_seconds)}.png"
                output_path = attachments_dir / filename
                
                if extract_frame(video_path, moment.timestamp_seconds, output_path):
                    moment.screenshot_path = output_path
                    print(f"    Screenshot: {filename}")
                else:
                    print(f"    Failed to extract frame at {moment.timestamp_str}")
        
        # Extract clips for dynamic moments (both GIF and MP4)
        if dynamic_to_extract:
            print(f"  Extracting {len(dynamic_to_extract)} clips (GIF + MP4)...")
            for moment in dynamic_to_extract:
                base_name = f"yt-{analysis.video_id}-{format_timestamp_filename(moment.timestamp_seconds)}-{moment.duration_seconds}s"
                gif_path = attachments_dir / f"{base_name}.gif"
                mp4_path = attachments_dir / f"{base_name}.mp4"
                
                # Extract GIF (for Obsidian preview)
                gif_success = extract_clip_gif(
                    video_path, 
                    moment.timestamp_seconds, 
                    moment.duration_seconds,
                    gif_path
                )
                if gif_success:
                    moment.gif_path = gif_path
                    print(f"    GIF: {gif_path.name}")
                else:
                    print(f"    Failed to extract GIF at {moment.timestamp_str}")
                
                # Extract MP4 (for AI consumption)
                mp4_success = extract_clip_mp4(
                    video_path,
                    moment.timestamp_seconds,
                    moment.duration_seconds,
                    mp4_path
                )
                if mp4_success:
                    moment.mp4_path = mp4_path
                    print(f"    MP4: {mp4_path.name}")
                else:
                    print(f"    Failed to extract MP4 at {moment.timestamp_str}")
    
    analysis.usage.media_extraction_time_seconds = time.time() - start_time


def generate_markdown_report(
    analyses: list[VideoAnalysis],
    title: str,
    output_dir: Path,
    attachments_dir: Path
) -> Path:
    """Generate the markdown report with all video analyses."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"youtube-analysis-{date_str}.md"
    
    # Handle duplicate filenames
    output_path = output_dir / filename
    counter = 1
    while output_path.exists():
        filename = f"youtube-analysis-{date_str}-{counter}.md"
        output_path = output_dir / filename
        counter += 1
    
    lines = []
    
    # Frontmatter
    lines.append("---")
    lines.append(f'title: "{title}"')
    lines.append(f"date: {date_str}")
    lines.append(f"videos_analyzed: {len(analyses)}")
    lines.append("type: youtube-analysis")
    lines.append("---")
    lines.append("")
    
    # Each video analysis
    for i, analysis in enumerate(analyses, 1):
        video_title = analysis.title or f"Video {i}"
        lines.append(f"## {video_title}")
        lines.append("")
        
        # Metadata
        lines.append(f"**URL:** {analysis.url}  ")
        if analysis.channel:
            lines.append(f"**Channel:** {analysis.channel}  ")
        if analysis.duration_seconds:
            lines.append(f"**Duration:** {format_duration(analysis.duration_seconds)}")
        lines.append("")
        
        # Summary
        if analysis.summary:
            lines.append("### Summary")
            lines.append("")
            lines.append(analysis.summary)
            lines.append("")
        
        # Key Points
        if analysis.key_points:
            lines.append("### Key Points")
            lines.append("")
            for timestamp, point in analysis.key_points:
                lines.append(f"- **[{timestamp}]** {point}")
            lines.append("")
        
        # Screenshots (static moments)
        screenshots = [m for m in analysis.static_moments if m.screenshot_path]
        if screenshots:
            lines.append("### Screenshots")
            lines.append("")
            for moment in screenshots:
                lines.append(f"**[{moment.timestamp_str}]** — {moment.description}")
                # Obsidian attachment link (just filename, Obsidian resolves it)
                lines.append(f"![[{moment.screenshot_path.name}]]")
                lines.append("")
        
        # Clips (dynamic moments) - embed GIF for autoplay, note MP4 exists
        clips = [m for m in analysis.dynamic_moments if m.gif_path]
        if clips:
            lines.append("### Clips")
            lines.append("")
            for moment in clips:
                lines.append(f"**[{moment.timestamp_str}]** ({moment.duration_seconds}s) — {moment.description}")
                # Embed GIF for autoplay in Obsidian
                lines.append(f"![[{moment.gif_path.name}]]")
                # Note that MP4 is also available for AI consumption
                if moment.mp4_path:
                    lines.append(f"*MP4 available: `{moment.mp4_path.name}`*")
                lines.append("")
        
        # Separator between videos
        if i < len(analyses):
            lines.append("---")
            lines.append("")
    
    # Write file
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))
    
    return output_path


def analyze_command(
    urls: list[str],
    output_dir: Path,
    title: str,
    custom_prompt: Optional[str],
    no_media: bool,
    max_screenshots: int,
    max_clips: int,
    model: str,
    profile: Optional[str]
) -> None:
    """Main analysis command."""
    api_key = get_api_key(profile)
    
    # Validate URLs
    valid_urls = []
    for url in urls:
        video_id = extract_video_id(url)
        if video_id:
            valid_urls.append(url)
        else:
            print(f"Warning: Invalid YouTube URL, skipping: {url}")
    
    if not valid_urls:
        print("Error: No valid YouTube URLs provided")
        sys.exit(1)
    
    total_start_time = time.time()
    
    print(f"Analyzing {len(valid_urls)} video(s)...")
    print(f"Model: {model}")
    print()
    
    analyses: list[VideoAnalysis] = []
    
    for i, url in enumerate(valid_urls, 1):
        video_id = extract_video_id(url)
        print(f"[{i}/{len(valid_urls)}] Analyzing: {url}")
        
        # Analyze with Gemini
        analysis = analyze_video_with_gemini(url, model, api_key, custom_prompt)
        
        # Extract media if enabled
        if not no_media and (analysis.static_moments or analysis.dynamic_moments):
            extract_media(analysis, DEFAULT_ATTACHMENTS_DIR, max_screenshots, max_clips)
        
        analyses.append(analysis)
        print()
    
    # Generate report
    print("Generating markdown report...")
    report_path = generate_markdown_report(analyses, title, output_dir, DEFAULT_ATTACHMENTS_DIR)
    
    total_time = time.time() - total_start_time
    
    # Calculate totals
    total_input_tokens = sum(a.usage.input_tokens for a in analyses)
    total_output_tokens = sum(a.usage.output_tokens for a in analyses)
    total_tokens = sum(a.usage.total_tokens for a in analyses)
    total_cost = sum(a.usage.cost_usd for a in analyses)
    total_analysis_time = sum(a.usage.analysis_time_seconds for a in analyses)
    total_media_time = sum(a.usage.media_extraction_time_seconds for a in analyses)
    total_screenshots = sum(
        len([m for m in a.static_moments if m.screenshot_path])
        for a in analyses
    )
    total_clips = sum(
        len([m for m in a.dynamic_moments if m.gif_path])
        for a in analyses
    )
    
    print()
    print(f"Report saved to: {report_path}")
    print()
    print("=" * 50)
    print("USAGE STATS")
    print("=" * 50)
    print(f"  Model: {model}")
    print(f"  Videos analyzed: {len(analyses)}")
    print(f"  Screenshots extracted: {total_screenshots}")
    print(f"  Clips extracted: {total_clips} (GIF + MP4 each)")
    print()
    print(f"  Input tokens: {total_input_tokens:,}")
    print(f"  Output tokens: {total_output_tokens:,}")
    print(f"  Total tokens: {total_tokens:,}")
    print()
    print(f"  Analysis time: {total_analysis_time:.1f}s")
    print(f"  Media extraction time: {total_media_time:.1f}s")
    print(f"  Total time: {total_time:.1f}s")
    print()
    print(f"  Estimated cost: ${total_cost:.4f}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze YouTube videos using Gemini and extract screenshots/clips"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze YouTube videos")
    analyze_parser.add_argument(
        "urls",
        nargs="+",
        help="YouTube video URLs to analyze"
    )
    analyze_parser.add_argument(
        "--output",
        type=Path,
        default=Path.cwd(),
        help="Output directory for the report (default: current directory)"
    )
    analyze_parser.add_argument(
        "--title",
        default="YouTube Video Analysis",
        help="Report title"
    )
    analyze_parser.add_argument(
        "--prompt",
        help="Additional analysis instructions"
    )
    analyze_parser.add_argument(
        "--no-media",
        action="store_true",
        help="Skip screenshot and clip extraction"
    )
    analyze_parser.add_argument(
        "--max-screenshots",
        type=int,
        default=5,
        help="Maximum screenshots per video (default: 5)"
    )
    analyze_parser.add_argument(
        "--max-clips",
        type=int,
        default=3,
        help="Maximum clips per video (default: 3)"
    )
    analyze_parser.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="Gemini model to use (default: gemini-2.5-flash)"
    )
    analyze_parser.add_argument(
        "--profile",
        help="Google API profile name"
    )
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        analyze_command(
            urls=args.urls,
            output_dir=args.output,
            title=args.title,
            custom_prompt=args.prompt,
            no_media=args.no_media,
            max_screenshots=args.max_screenshots,
            max_clips=args.max_clips,
            model=args.model,
            profile=args.profile,
        )


if __name__ == "__main__":
    main()
