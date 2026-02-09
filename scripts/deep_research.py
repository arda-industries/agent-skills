#!/usr/bin/env python3
"""
Deep Research CLI

Interact with OpenAI's deep research API to conduct comprehensive,
citation-backed research on companies, people, products, or custom topics.

Usage:
    poetry run python scripts/deep_research.py submit --template company --topic "OpenAI"
    poetry run python scripts/deep_research.py status <response_id>
    poetry run python scripts/deep_research.py download <response_id> --output ./reports/
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from openai import OpenAI

# Directory containing this script
SCRIPT_DIR = Path(__file__).parent.resolve()
# Skills directory with prompts
SKILLS_DIR = SCRIPT_DIR.parent / ".cursor" / "skills" / "x-deep-research"
PROMPTS_DIR = SKILLS_DIR / "prompts"
# Config file for profiles
PROFILES_PATH = Path.home() / ".config" / "openai" / "profiles.json"


def get_api_key(profile: Optional[str] = None) -> str:
    """Get OpenAI API key from profiles.json config file.
    
    Priority:
    1. Explicit --profile argument
    2. Default profile from profiles.json
    3. OPENAI_API_KEY environment variable (fallback)
    """
    # Load profiles config if it exists
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
            if not api_key or api_key.startswith("sk-proj-REPLACE"):
                print(f"Error: API key for profile '{profile}' is not configured.")
                print(f"Edit {PROFILES_PATH} and add your API key.")
                sys.exit(1)
            
            return api_key
        
        # Use default profile
        default_profile = config.get("default")
        if default_profile and default_profile in profiles:
            api_key = profiles[default_profile].get("api_key")
            if api_key and not api_key.startswith("sk-proj-REPLACE"):
                return api_key
            else:
                print(f"Error: API key for default profile '{default_profile}' is not configured.")
                print(f"Edit {PROFILES_PATH} and replace the placeholder with your API key.")
                sys.exit(1)
    
    # Fall back to environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    # No API key found anywhere
    print("Error: No API key found.")
    print()
    print("Option 1: Configure profiles.json (recommended)")
    print(f"  Edit: {PROFILES_PATH}")
    print()
    print("Option 2: Set environment variable")
    print("  export OPENAI_API_KEY='sk-proj-...'")
    sys.exit(1)


def load_prompt(template: str, topic: str) -> str:
    """Load and combine base prompt with template-specific prompt."""
    base_path = PROMPTS_DIR / "base.md"
    template_path = PROMPTS_DIR / f"{template}.md"
    
    if not base_path.exists():
        print(f"Error: Base prompt not found at {base_path}")
        sys.exit(1)
    
    if not template_path.exists():
        print(f"Error: Template '{template}' not found at {template_path}")
        available = [p.stem for p in PROMPTS_DIR.glob("*.md") if p.stem != "base"]
        print(f"Available templates: {', '.join(available)}")
        sys.exit(1)
    
    base_prompt = base_path.read_text()
    template_prompt = template_path.read_text()
    
    # Replace {topic} placeholder in template
    template_prompt = template_prompt.replace("{topic}", topic)
    
    # Combine prompts
    combined = f"{base_prompt}\n\n---\n\n{template_prompt}"
    return combined


def submit_research(
    template: str,
    topic: str,
    query: Optional[str],
    profile: Optional[str],
    output_dir: Path,
    model: str
) -> None:
    """Submit a deep research query."""
    api_key = get_api_key(profile)
    client = OpenAI(api_key=api_key, timeout=3600)
    
    # Build the prompt
    if template == "custom":
        if not query:
            print("Error: --query is required for custom template")
            sys.exit(1)
        # Load just base prompt and append custom query
        base_path = PROMPTS_DIR / "base.md"
        base_prompt = base_path.read_text() if base_path.exists() else ""
        full_prompt = f"{base_prompt}\n\n---\n\n{query}"
    else:
        if not topic:
            print(f"Error: --topic is required for {template} template")
            sys.exit(1)
        full_prompt = load_prompt(template, topic)
    
    print(f"Submitting research query...")
    print(f"  Model: {model}")
    print(f"  Template: {template}")
    if topic:
        print(f"  Topic: {topic}")
    print()
    
    try:
        response = client.responses.create(
            model=model,
            input=full_prompt,
            background=True,
            tools=[{"type": "web_search_preview"}],
        )
        
        response_id = response.id
        status = response.status
        
        print("Research submitted successfully!")
        print(f"  Response ID: {response_id}")
        print(f"  Status: {status}")
        print()
        print("To check status:")
        print(f"  poetry run python scripts/deep_research.py status {response_id}")
        print()
        print("Research typically takes 5-30 minutes.")
        
        # Save metadata for later
        metadata = {
            "response_id": response_id,
            "template": template,
            "topic": topic or query[:50],
            "model": model,
            "submitted_at": datetime.now().isoformat(),
            "output_dir": str(output_dir),
        }
        
        # Save to a tracking file
        tracking_dir = SKILLS_DIR / ".tracking"
        tracking_dir.mkdir(exist_ok=True)
        tracking_file = tracking_dir / f"{response_id}.json"
        with open(tracking_file, "w") as f:
            json.dump(metadata, f, indent=2)
        
    except Exception as e:
        print(f"Error submitting research: {e}")
        sys.exit(1)


def check_status(response_id: str, profile: Optional[str]) -> None:
    """Check status of a research query."""
    api_key = get_api_key(profile)
    client = OpenAI(api_key=api_key, timeout=60)
    
    try:
        response = client.responses.retrieve(response_id)
        status = response.status
        
        print(f"Response ID: {response_id}")
        print(f"Status: {status}")
        
        # Try to load tracking metadata for timing info
        tracking_file = SKILLS_DIR / ".tracking" / f"{response_id}.json"
        if tracking_file.exists():
            with open(tracking_file) as f:
                metadata = json.load(f)
            submitted_at = datetime.fromisoformat(metadata["submitted_at"])
            elapsed = datetime.now() - submitted_at
            elapsed_mins = int(elapsed.total_seconds() / 60)
            print(f"Elapsed: {elapsed_mins} minutes")
        
        if status == "completed":
            print()
            print("Research complete! To download results:")
            print(f"  poetry run python scripts/deep_research.py download {response_id}")
        elif status == "failed":
            print()
            print("Research failed. Check the error details in the response.")
            if hasattr(response, "error") and response.error:
                print(f"Error: {response.error}")
        elif status == "cancelled":
            print()
            print("Research was cancelled.")
        else:
            print()
            print("Still in progress. Check again in a few minutes.")
            
    except Exception as e:
        print(f"Error checking status: {e}")
        sys.exit(1)


# Pricing per million tokens (as of Jan 2026)
MODEL_PRICING = {
    "o3-deep-research": {"input": 10.00, "output": 40.00},
    "o4-mini-deep-research": {"input": 2.00, "output": 8.00},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD based on model and token counts."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["o3-deep-research"])
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


def download_results(response_id: str, profile: Optional[str], output_dir: Path) -> None:
    """Download and format research results as markdown."""
    api_key = get_api_key(profile)
    client = OpenAI(api_key=api_key, timeout=60)
    
    try:
        response = client.responses.retrieve(response_id)
        
        if response.status != "completed":
            print(f"Error: Research not complete. Status: {response.status}")
            sys.exit(1)
        
        # Extract the final message content
        output_text = None
        annotations = []
        
        for item in response.output:
            if item.type == "message":
                for content in item.content:
                    if content.type == "output_text":
                        output_text = content.text
                        if hasattr(content, "annotations"):
                            annotations = content.annotations or []
                        break
        
        if not output_text:
            print("Error: No output text found in response")
            sys.exit(1)
        
        # Extract usage info
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, "usage") and response.usage:
            input_tokens = getattr(response.usage, "input_tokens", 0) or 0
            output_tokens = getattr(response.usage, "output_tokens", 0) or 0
        
        # Load metadata for filename generation
        tracking_file = SKILLS_DIR / ".tracking" / f"{response_id}.json"
        metadata = {}
        if tracking_file.exists():
            with open(tracking_file) as f:
                metadata = json.load(f)
        
        # Calculate duration
        duration_mins = 0
        if "submitted_at" in metadata:
            submitted_at = datetime.fromisoformat(metadata["submitted_at"])
            duration = datetime.now() - submitted_at
            duration_mins = round(duration.total_seconds() / 60, 1)
        
        # Calculate cost
        model = metadata.get("model", "o3-deep-research")
        cost_usd = calculate_cost(model, input_tokens, output_tokens)
        
        # Update tracking file with usage info
        metadata["completed_at"] = datetime.now().isoformat()
        metadata["duration_minutes"] = duration_mins
        metadata["input_tokens"] = input_tokens
        metadata["output_tokens"] = output_tokens
        metadata["total_tokens"] = input_tokens + output_tokens
        metadata["cost_usd"] = round(cost_usd, 4)
        metadata["sources_count"] = len(annotations)
        
        with open(tracking_file, "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Generate filename
        topic = metadata.get("topic", "research")
        # Sanitize topic for filename
        safe_topic = re.sub(r"[^\w\s-]", "", topic.lower())
        safe_topic = re.sub(r"[\s]+", "-", safe_topic)[:50]
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{safe_topic}-research-{date_str}.md"
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename
        
        # Build the markdown document
        markdown_parts = []
        
        # Frontmatter
        markdown_parts.append("---")
        markdown_parts.append(f"title: \"Research: {metadata.get('topic', 'Unknown')}\"")
        markdown_parts.append(f"date: {date_str}")
        markdown_parts.append(f"model: {model}")
        markdown_parts.append(f"template: {metadata.get('template', 'unknown')}")
        markdown_parts.append(f"response_id: {response_id}")
        markdown_parts.append("---")
        markdown_parts.append("")
        
        # Main content
        markdown_parts.append(output_text)
        markdown_parts.append("")
        
        # Sources section
        if annotations:
            markdown_parts.append("---")
            markdown_parts.append("")
            markdown_parts.append("## Sources")
            markdown_parts.append("")
            
            # Deduplicate sources by URL
            seen_urls = set()
            unique_sources = []
            for ann in annotations:
                if hasattr(ann, "url") and ann.url and ann.url not in seen_urls:
                    seen_urls.add(ann.url)
                    unique_sources.append(ann)
            
            for i, source in enumerate(unique_sources, 1):
                title = getattr(source, "title", "Untitled")
                url = getattr(source, "url", "")
                markdown_parts.append(f"{i}. [{title}]({url})")
            
            markdown_parts.append("")
        
        # Write the file
        output_path.write_text("\n".join(markdown_parts))
        
        # Print results with cost info
        print(f"Research report saved to:")
        print(f"  {output_path}")
        print()
        print(f"Sources cited: {len(annotations)}")
        print()
        print("=== Usage Stats ===")
        print(f"  Model: {model}")
        print(f"  Duration: {duration_mins} minutes")
        print(f"  Input tokens: {input_tokens:,}")
        print(f"  Output tokens: {output_tokens:,}")
        print(f"  Total tokens: {input_tokens + output_tokens:,}")
        print(f"  Cost: ${cost_usd:.4f}")
        
    except Exception as e:
        print(f"Error downloading results: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Deep Research CLI - Conduct comprehensive research using OpenAI's deep research API"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Submit command
    submit_parser = subparsers.add_parser("submit", help="Submit a new research query")
    submit_parser.add_argument(
        "--template",
        choices=["company", "person", "product", "custom"],
        default="company",
        help="Research template to use (default: company)"
    )
    submit_parser.add_argument(
        "--topic",
        help="Research topic (required for non-custom templates)"
    )
    submit_parser.add_argument(
        "--query",
        help="Full custom query (for custom template)"
    )
    submit_parser.add_argument(
        "--profile",
        help="OpenAI profile name from ~/.config/openai/profiles.json"
    )
    submit_parser.add_argument(
        "--output",
        type=Path,
        default=Path.cwd(),
        help="Output directory for results (default: current directory)"
    )
    submit_parser.add_argument(
        "--model",
        choices=["o3-deep-research", "o4-mini-deep-research"],
        default="o3-deep-research",
        help="Model to use (default: o3-deep-research)"
    )
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check status of a research query")
    status_parser.add_argument("response_id", help="Response ID from submit command")
    status_parser.add_argument(
        "--profile",
        help="OpenAI profile name"
    )
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Download completed research results")
    download_parser.add_argument("response_id", help="Response ID from submit command")
    download_parser.add_argument(
        "--profile",
        help="OpenAI profile name"
    )
    download_parser.add_argument(
        "--output",
        type=Path,
        default=Path.cwd(),
        help="Output directory for results (default: current directory)"
    )
    
    args = parser.parse_args()
    
    if args.command == "submit":
        submit_research(
            template=args.template,
            topic=args.topic,
            query=args.query,
            profile=args.profile,
            output_dir=args.output,
            model=args.model,
        )
    elif args.command == "status":
        check_status(
            response_id=args.response_id,
            profile=args.profile,
        )
    elif args.command == "download":
        download_results(
            response_id=args.response_id,
            profile=args.profile,
            output_dir=args.output,
        )


if __name__ == "__main__":
    main()
