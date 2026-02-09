---
name: x-notion-mcp
description: Spec + workflow for attaching local screenshots/clips to Notion pages (private, Notion-hosted) when MCP tools lack file-upload support.
---

# Notion MCP (Spec Placeholder)

This skill is a **SPEC / placeholder** for implementing a reliable workflow to **upload local media (PNG/GIF/MP4/etc.) into Notion privately** and embed it into a Notion page, even when the current Notion MCP toolset does not expose file upload APIs.

## Problem Statement

We often generate local artifacts (screenshots, GIFs, clips) in `~/brain/obsidian/.../attachments/` and want them embedded in a Notion page. Notion’s API supports direct uploads, but our current MCP tools typically only support page CRUD via Notion-flavored markdown and do **not** expose:

- File Upload API (create/send/complete/retrieve)
- Block children append/update (JSON block payloads)

Therefore we need a **hybrid** approach that preserves privacy (no public hosting) and integrates smoothly with the existing MCP workflow.

## Requirements

- **R1: No public hosting**: Do not upload to Imgur/S3/CDNs. Files must be **Notion-hosted** uploads.
- **R2: Private workspace access**: Uploaded media must be accessible only to users with access to the page/workspace.
- **R3: Deterministic embedding**: Embed media at a specific location in a page (e.g., under “Video Demo Analysis”), not only at end-of-page.
- **R4: Idempotency**: Re-runs should not duplicate media blocks. Detect existing media blocks / use a marker section.
- **R5: Safe defaults**: Never delete content or move pages/databases without explicit instruction.
- **R6: Handle limits**: Respect workspace upload limits (free plans may have small per-file caps).

## Key Notion API Capabilities (Non-MCP)

Notion supports uploading local files using the File Upload APIs:

- Create: `POST /v1/file_uploads` ([docs](https://developers.notion.com/reference/create-a-file-upload))
- Send: `POST /v1/file_uploads/{id}/send` as `multipart/form-data` ([docs](https://developers.notion.com/reference/send-a-file-upload))
- File object types (including `file_upload`) ([docs](https://developers.notion.com/reference/file-object))
- Append blocks to a page: `PATCH /v1/blocks/{block_id}/children` ([docs](https://developers.notion.com/reference/patch-block-children))

Once a file upload reaches `status="uploaded"`, it can be attached to media blocks using:

```json
{
  "type": "file_upload",
  "file_upload": { "id": "<file_upload_uuid>" }
}
```

## Proposed Architecture

### Option A (Recommended): Add a local helper script in `agent-instructions`

Create a script (Python preferred) that:

1. **Uploads local files** to Notion via File Upload API
2. **Appends image/video blocks** to a target page at a chosen insertion point
3. Optionally returns a “receipt” (uploaded IDs, block IDs, file sizes)

Then continue using MCP for everything else (creating/updating pages via markdown).

### Option B: Extend the Notion MCP server

Add MCP tools (or enhance existing ones) to support:

- `notion-file-uploads-create`
- `notion-file-uploads-send`
- `notion-file-uploads-complete`
- `notion-block-children-append`

This is higher leverage but requires MCP server development and rollout.

## Authentication Strategy

- Use a Notion integration token (`NOTION_API_KEY`) with:
  - Access to the target page
  - “insert content” capability (required for appending blocks)
- Keep secrets out of git. Read from environment or a local config (e.g. `~/.config/notion/profiles.json`).

## Insertion Strategy (Deterministic Placement)

Goal: Insert media under a specific section such as “Video Demo Analysis”.

Approach:

1. Retrieve the page’s block children via the Notion API (not MCP) and find:
   - A heading block matching a target title, OR
   - A marker paragraph like `<!-- MEDIA: C-Infinity -->`
2. Append blocks with `position: { type: "after_block", after_block: { id: "<block_id>" } }`
3. If marker/heading not found, fall back to appending at end.

## Idempotency Strategy

Insert a marker block the first time:

- A paragraph block containing a stable identifier, e.g. `MEDIA_SECTION: c-infinity-autoassembler`

On rerun:

- Find the marker
- Enumerate subsequent blocks until next heading of same/higher level
- If the expected images already exist (by caption or filename in adjacent text), skip

## Media Mapping Rules

- **PNG/JPG/WebP** → image blocks
- **GIF** → image blocks (renders inline)
- **MP4** → video blocks (or file blocks if video fails)

Captions should include:

- Original filename
- Source timestamp (if available)
- Short description (from analyzer output)

## CLI Interface (Suggested)

```bash
poetry run python scripts/notion_media_push.py \
  --page "https://www.notion.so/<page-id>" \
  --section "Video Demo Analysis" \
  --media ~/brain/obsidian/Timatron/attachments/yt-Bx3hMd7Fuew-*.png \
  --media ~/brain/obsidian/Timatron/attachments/yt-Bx3hMd7Fuew-*.gif \
  --dry-run
```

## Validation / Pre-flight Checks

- Confirm page is accessible to token (fetch page).
- Confirm per-file size is under workspace max (see “working with files and media” guide).
- Confirm upload status transitions to `uploaded` before attaching.
- Confirm blocks were appended where expected.

## Risks / Gotchas

- Notion-hosted file URLs are **time-limited signed URLs** when fetched (this is normal for Notion “file” objects). The files remain private, but URLs can be accessed while valid.
- Free workspaces may cap uploads to **~5 MiB/file** (verify programmatically).
- Rate limits and block child append limits (max 100 blocks per request).
- Different Notion API versions; prefer latest (currently `2025-09-03` per docs).

## Implementation Checklist (Future Work)

- [ ] Add `scripts/notion_media_push.py` using `requests` (multipart/form-data for send)
- [ ] Add config loading for token (env + optional profiles file)
- [ ] Add block retrieval + insertion point resolution
- [ ] Add idempotency marker strategy
- [ ] Add unit-ish “dry-run” mode to print planned actions without changes
- [ ] Add docs/examples for common workflows (e.g., pushing YouTube analyzer outputs)

