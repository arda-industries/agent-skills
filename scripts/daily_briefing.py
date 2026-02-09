#!/usr/bin/env python3
"""
Daily Briefing CLI

Fetch health data from TimTracker and generate a daily briefing
with assessments for sleep, exercise, diet, and mindfulness.

Usage:
    poetry run python scripts/daily_briefing.py
    poetry run python scripts/daily_briefing.py --weeks 2  # Look back 2 weeks
    poetry run python scripts/daily_briefing.py --json     # Output raw JSON data
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Config file location
CONFIG_PATH = Path.home() / ".config" / "timtracker" / "config.json"

# Health targets for assessment
TARGETS = {
    "sleep_hours": 7.5,  # Target hours per night
    "sleep_min": 6.0,    # Minimum acceptable
    "exercise_weekly": 150,  # Minutes per week target
    "diet_score": 7.0,   # Target daily score (1-10)
    "mindful_daily": 10,  # Target minutes per day
}


def load_config() -> dict:
    """Load TimTracker API configuration."""
    if not CONFIG_PATH.exists():
        print(f"Error: Config file not found at {CONFIG_PATH}")
        print()
        print("Create the config file with:")
        print(f"  mkdir -p {CONFIG_PATH.parent}")
        print(f"  cat > {CONFIG_PATH} << 'EOF'")
        print('  {')
        print('    "api_url": "https://timtracker-api.vercel.app",')
        print('    "api_key": "your-gpt-api-key-here"')
        print('  }')
        print("  EOF")
        sys.exit(1)
    
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    
    if not config.get("api_key") or config["api_key"] == "your-gpt-api-key-here":
        print(f"Error: API key not configured in {CONFIG_PATH}")
        print("Update the api_key field with your GPT_API_KEY from Vercel.")
        sys.exit(1)
    
    return config


def fetch_weekly_summary(config: dict, offset: int = 0) -> dict:
    """Fetch weekly summary data from TimTracker API."""
    api_url = config.get("api_url", "https://timtracker-api.vercel.app")
    api_key = config["api_key"]
    
    url = f"{api_url}/api/weekly-summary?offset={offset}"
    
    req = Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    
    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        if e.code == 401:
            print("Error: Authentication failed. Check your API key.")
        else:
            print(f"Error: API request failed with status {e.code}")
        sys.exit(1)
    except URLError as e:
        print(f"Error: Could not connect to API: {e.reason}")
        sys.exit(1)


def assess_sleep(days: list[dict]) -> dict:
    """Analyze sleep data and generate assessment."""
    sleep_values = [d["sleepHours"] for d in days if d.get("sleepHours") is not None]
    
    if not sleep_values:
        return {
            "status": "no_data",
            "message": "No sleep data recorded this week.",
            "emoji": "⚪",
        }
    
    avg_sleep = sum(sleep_values) / len(sleep_values)
    days_tracked = len(sleep_values)
    min_sleep = min(sleep_values)
    max_sleep = max(sleep_values)
    
    # Calculate consistency (standard deviation)
    variance = sum((x - avg_sleep) ** 2 for x in sleep_values) / len(sleep_values)
    std_dev = variance ** 0.5
    
    # Determine status
    if avg_sleep >= TARGETS["sleep_hours"]:
        status = "good"
        emoji = "🟢"
    elif avg_sleep >= TARGETS["sleep_min"]:
        status = "fair"
        emoji = "🟡"
    else:
        status = "poor"
        emoji = "🔴"
    
    # Build assessment message
    parts = []
    parts.append(f"Averaged **{avg_sleep:.1f} hours/night** across {days_tracked} days tracked.")
    
    if std_dev > 1.0:
        parts.append(f"Sleep was inconsistent (ranging from {min_sleep:.1f}h to {max_sleep:.1f}h).")
    elif std_dev < 0.5:
        parts.append("Sleep schedule was very consistent.")
    
    if avg_sleep < TARGETS["sleep_hours"]:
        deficit = (TARGETS["sleep_hours"] - avg_sleep) * days_tracked
        parts.append(f"Running a sleep deficit of about {deficit:.0f} hours for the week.")
    
    return {
        "status": status,
        "emoji": emoji,
        "message": " ".join(parts),
        "avg_hours": round(avg_sleep, 1),
        "days_tracked": days_tracked,
        "consistency": round(std_dev, 2),
    }


def assess_exercise(days: list[dict]) -> dict:
    """Analyze exercise data and generate assessment."""
    exercise_values = [d["exercise"] for d in days if d.get("exercise") is not None]
    
    if not exercise_values:
        return {
            "status": "no_data",
            "message": "No exercise data recorded this week.",
            "emoji": "⚪",
        }
    
    total_minutes = sum(exercise_values)
    active_days = len(exercise_values)
    avg_per_session = total_minutes / active_days if active_days > 0 else 0
    
    # Collect workout types
    workout_types = []
    for d in days:
        if d.get("workouts"):
            for w in d["workouts"]:
                if w.get("type") and w["type"] not in workout_types:
                    workout_types.append(w["type"])
    
    # Determine status
    if total_minutes >= TARGETS["exercise_weekly"]:
        status = "good"
        emoji = "🟢"
    elif total_minutes >= TARGETS["exercise_weekly"] * 0.7:
        status = "fair"
        emoji = "🟡"
    else:
        status = "poor"
        emoji = "🔴"
    
    # Build assessment message
    parts = []
    parts.append(f"**{total_minutes:.0f} minutes** of exercise across {active_days} days.")
    
    if workout_types:
        types_str = ", ".join(workout_types[:4])
        if len(workout_types) > 4:
            types_str += f" (+{len(workout_types) - 4} more)"
        parts.append(f"Activities: {types_str}.")
    
    if total_minutes < TARGETS["exercise_weekly"]:
        deficit = TARGETS["exercise_weekly"] - total_minutes
        parts.append(f"Need {deficit:.0f} more minutes to hit weekly target.")
    else:
        surplus = total_minutes - TARGETS["exercise_weekly"]
        parts.append(f"Exceeding weekly target by {surplus:.0f} minutes!")
    
    return {
        "status": status,
        "emoji": emoji,
        "message": " ".join(parts),
        "total_minutes": round(total_minutes),
        "active_days": active_days,
        "workout_types": workout_types,
    }


def assess_diet(days: list[dict]) -> dict:
    """Analyze diet data and generate assessment."""
    diet_values = [d["dietScore"] for d in days if d.get("dietScore") is not None]
    
    if not diet_values:
        return {
            "status": "no_data",
            "message": "No diet scores recorded this week.",
            "emoji": "⚪",
        }
    
    avg_score = sum(diet_values) / len(diet_values)
    days_tracked = len(diet_values)
    min_score = min(diet_values)
    max_score = max(diet_values)
    
    # Count good vs poor days
    good_days = sum(1 for v in diet_values if v >= TARGETS["diet_score"])
    poor_days = sum(1 for v in diet_values if v < 5)
    
    # Determine status
    if avg_score >= TARGETS["diet_score"]:
        status = "good"
        emoji = "🟢"
    elif avg_score >= 5:
        status = "fair"
        emoji = "🟡"
    else:
        status = "poor"
        emoji = "🔴"
    
    # Build assessment message
    parts = []
    parts.append(f"Average diet score: **{avg_score:.1f}/10** across {days_tracked} days.")
    
    if good_days == days_tracked:
        parts.append("All tracked days met the health target!")
    elif poor_days > 0:
        parts.append(f"{poor_days} day(s) with scores below 5.")
    
    if max_score - min_score > 4:
        parts.append(f"Wide variation in scores ({min_score:.0f} to {max_score:.0f}).")
    
    return {
        "status": status,
        "emoji": emoji,
        "message": " ".join(parts),
        "avg_score": round(avg_score, 1),
        "days_tracked": days_tracked,
        "good_days": good_days,
    }


def assess_mindfulness(days: list[dict]) -> dict:
    """Analyze mindfulness data and generate assessment."""
    mindful_values = [d["mindfulMinutes"] for d in days if d.get("mindfulMinutes") is not None]
    
    if not mindful_values:
        return {
            "status": "no_data",
            "message": "No mindfulness data recorded this week.",
            "emoji": "⚪",
        }
    
    total_minutes = sum(mindful_values)
    days_practiced = len(mindful_values)
    avg_per_day = total_minutes / 7  # Average across full week
    
    # Days meeting target
    target_days = sum(1 for v in mindful_values if v >= TARGETS["mindful_daily"])
    
    # Determine status
    if avg_per_day >= TARGETS["mindful_daily"]:
        status = "good"
        emoji = "🟢"
    elif avg_per_day >= TARGETS["mindful_daily"] * 0.5:
        status = "fair"
        emoji = "🟡"
    else:
        status = "poor"
        emoji = "🔴"
    
    # Build assessment message
    parts = []
    parts.append(f"**{total_minutes:.0f} minutes** of mindfulness across {days_practiced} days.")
    
    if days_practiced < 7:
        missing = 7 - days_practiced
        parts.append(f"{missing} day(s) without recorded practice.")
    
    if target_days == days_practiced and days_practiced >= 5:
        parts.append("Great consistency meeting daily targets!")
    elif target_days > 0:
        parts.append(f"{target_days} day(s) hit the {TARGETS['mindful_daily']} min target.")
    
    return {
        "status": status,
        "emoji": emoji,
        "message": " ".join(parts),
        "total_minutes": round(total_minutes),
        "days_practiced": days_practiced,
        "avg_per_day": round(avg_per_day, 1),
    }


def generate_summary(assessments: dict) -> str:
    """Generate overall summary based on all assessments."""
    statuses = [a["status"] for a in assessments.values() if a["status"] != "no_data"]
    
    if not statuses:
        return "Insufficient data to generate a health summary. Try logging more activities in TimTracker."
    
    good_count = statuses.count("good")
    poor_count = statuses.count("poor")
    total = len(statuses)
    
    parts = []
    
    if good_count == total:
        parts.append("Excellent week across all tracked categories!")
    elif good_count >= total / 2:
        parts.append(f"Solid week with {good_count}/{total} categories meeting targets.")
    elif poor_count >= total / 2:
        parts.append(f"Challenging week — {poor_count}/{total} categories below target.")
    else:
        parts.append("Mixed results this week.")
    
    # Add specific recommendations
    recs = []
    if assessments["sleep"]["status"] == "poor":
        recs.append("prioritize earlier bedtimes")
    if assessments["exercise"]["status"] == "poor":
        recs.append("schedule workout sessions")
    if assessments["diet"]["status"] == "poor":
        recs.append("plan healthier meals")
    if assessments["mindfulness"]["status"] == "poor":
        recs.append("set a daily meditation reminder")
    
    if recs:
        parts.append(f"Focus areas: {', '.join(recs)}.")
    
    return " ".join(parts)


def format_briefing(data: dict, assessments: dict, summary: str) -> str:
    """Format the briefing as markdown."""
    lines = []
    
    # Date range header
    lines.append(f"*Data from {data['startDateStr']} to {data['endDateStr']}*")
    lines.append("")
    
    # Sleep section
    sleep = assessments["sleep"]
    lines.append(f"#### Sleep {sleep['emoji']}")
    lines.append(sleep["message"])
    lines.append("")
    
    # Exercise section
    exercise = assessments["exercise"]
    lines.append(f"#### Exercise {exercise['emoji']}")
    lines.append(exercise["message"])
    lines.append("")
    
    # Diet section
    diet = assessments["diet"]
    lines.append(f"#### Diet {diet['emoji']}")
    lines.append(diet["message"])
    lines.append("")
    
    # Mindfulness section
    mindful = assessments["mindfulness"]
    lines.append(f"#### Mindfulness {mindful['emoji']}")
    lines.append(mindful["message"])
    lines.append("")
    
    # Summary section
    lines.append("#### Summary")
    lines.append(summary)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a daily health briefing from TimTracker data"
    )
    parser.add_argument(
        "--weeks",
        type=int,
        default=0,
        help="Number of weeks to look back (default: 0 = current week)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON data instead of markdown briefing"
    )
    
    args = parser.parse_args()
    
    # Load config and fetch data
    config = load_config()
    data = fetch_weekly_summary(config, offset=args.weeks)
    
    if args.json:
        print(json.dumps(data, indent=2))
        return
    
    # Generate assessments
    days = data.get("days", [])
    
    assessments = {
        "sleep": assess_sleep(days),
        "exercise": assess_exercise(days),
        "diet": assess_diet(days),
        "mindfulness": assess_mindfulness(days),
    }
    
    summary = generate_summary(assessments)
    
    # Format and output briefing
    briefing = format_briefing(data, assessments, summary)
    print(briefing)


if __name__ == "__main__":
    main()
