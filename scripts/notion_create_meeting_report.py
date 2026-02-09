#!/usr/bin/env python3
"""
Create a new row (page) in a Notion database by calling the Notion REST API directly.

Use this when the Notion MCP fails to create pages with a database parent (e.g. parent
received as string). Requires NOTION_API_KEY and a Notion integration with access to
the target database.

Usage:
  export NOTION_API_KEY=secret_...
  echo '<json payload>' | python notion_create_meeting_report.py
  # or
  python notion_create_meeting_report.py --payload-file report.json

Payload JSON (all keys optional except parent.data_source_id and properties.Title):
  {
    "parent": { "data_source_id": "2f2a2ca0-58dd-46d7-9d51-596aa954a03c" },
    "properties": {
      "Title": "Meeting title",
      "Date": "2026-02-06",
      "Status": "Draft",
      "External attendees": "Name One, Name Two",
      "BLUF": "Bottom line summary.",
      "Action items": "Item one. Item two."
    },
    "content_markdown": "## Attendees\n- **Internal:** ...\n\n## Summary\n..."
  }

Notion API: https://developers.notion.com/reference/post-page
Parent for DB rows: https://developers.notion.com/reference/parent-object (data_source_id)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


NOTION_API_BASE = "https://api.notion.com"
NOTION_VERSION = "2025-09-03"
MEETING_REPORTS_DATA_SOURCE_ID = "2f2a2ca0-58dd-46d7-9d51-596aa954a03c"


def rich_text(content: str, bold: bool = False) -> dict:
    return {
        "type": "text",
        "text": {"content": content[:2000], "link": None},
        "annotations": {
            "bold": bold,
            "italic": False,
            "strikethrough": False,
            "underline": False,
            "code": False,
            "color": "default",
        },
    }


def md_to_blocks(md: str) -> list[dict]:
    """Convert simple markdown to Notion block objects (heading_2, paragraph, bulleted_list_item)."""
    blocks = []
    for line in md.strip().split("\n"):
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [rich_text(line[3:].strip())],
                    "color": "default",
                    "is_toggleable": False,
                },
            })
        elif line.startswith("- "):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [rich_text(line[2:].strip())],
                    "color": "default",
                },
            })
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [rich_text(line)],
                    "color": "default",
                },
            })
    return blocks


def sqlite_properties_to_notion_api(properties: dict) -> dict:
    """Convert simple key-value properties to Notion API property value format."""
    out = {}
    for key, value in properties.items():
        if value is None or value == "":
            continue
        if key == "Title":
            out[key] = {
                "title": [rich_text(str(value))],
            }
        elif key == "Date":
            out[key] = {
                "date": {"start": str(value), "end": None, "time_zone": None},
            }
        elif key == "Status":
            out[key] = {
                "status": {"name": str(value)},
            }
        elif key in ("External attendees", "BLUF", "Action items"):
            out[key] = {
                "rich_text": [rich_text(str(value))],
            }
        elif key == "Attendees":
            if isinstance(value, list):
                out[key] = {
                    "people": [{"id": uid} if isinstance(uid, str) else uid for uid in value],
                }
            else:
                out[key] = {"rich_text": [rich_text(str(value))]}
        else:
            out[key] = {"rich_text": [rich_text(str(value))]}
    return out


def create_page(
    token: str,
    parent: dict,
    properties: dict,
    children: list[dict] | None = None,
) -> dict:
    """POST /v1/pages to create a new page under a data source."""
    body = {
        "parent": {
            "type": "data_source_id",
            "data_source_id": parent.get("data_source_id", MEETING_REPORTS_DATA_SOURCE_ID),
        },
        "properties": sqlite_properties_to_notion_api(properties),
    }
    if children:
        body["children"] = children

    req = urllib.request.Request(
        f"{NOTION_API_BASE}/v1/pages",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            err = json.loads(body)
            msg = err.get("message", body)
        except Exception:
            msg = body
        raise SystemExit(f"Notion API error {e.code}: {msg}") from e


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Notion meeting report row via REST API")
    parser.add_argument("--payload-file", type=str, help="Read JSON payload from file")
    parser.add_argument("--data-source-id", type=str, default=MEETING_REPORTS_DATA_SOURCE_ID,
                        help="Data source (collection) ID of the target database")
    args = parser.parse_args()

    token = os.environ.get("NOTION_API_KEY")
    if not token:
        raise SystemExit("NOTION_API_KEY is not set. Create an integration at https://www.notion.so/my-integrations and share the database with it.")

    if args.payload_file:
        with open(args.payload_file, encoding="utf-8") as f:
            payload = json.load(f)
    else:
        payload = json.load(sys.stdin)

    parent = payload.get("parent", {})
    if "data_source_id" not in parent:
        parent["data_source_id"] = args.data_source_id
    properties = payload.get("properties", {})
    if not properties or "Title" not in properties:
        raise SystemExit("Payload must include properties.Title")

    content_md = payload.get("content_markdown", "")
    children = md_to_blocks(content_md) if content_md else None

    result = create_page(token, parent, properties, children)
    page_id = result.get("id", "").replace("-", "")
    url = f"https://www.notion.so/{result.get('url', page_id)}" if result.get("url") else f"https://www.notion.so/{page_id}"
    print(url)
    if os.environ.get("NOTION_CREATE_VERBOSE"):
        print(json.dumps(result, indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
