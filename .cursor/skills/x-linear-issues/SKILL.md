---
name: x-linear-issues
description: Create and manage Linear issues from documents, notes, or conversations. Use when asked to create tickets, file issues, or work with Linear.
---

## Goal

Create, update, and manage Linear issues from source documents (Obsidian notes, markdown files, Slack threads, etc.) using the Linear MCP integration.

## Prerequisites

- **Linear MCP must be connected** — the `user-linear-*` tools must be available
- If Linear MCP is not available, guide the user to set it up:
  1. Open Cursor Settings (`Cmd+Shift+J`)
  2. Go to **MCP** section
  3. Add Linear with config: `{"command":"npx","args":["-y","mcp-remote","https://mcp.linear.app/mcp"]}`
  4. Authenticate via the browser OAuth flow

## Workflow: Creating issues from a document

### Step 1 — Identify the source section

When given a document to extract issues from:

- Read the specified file/section
- Look for checkbox items (`- [ ] ...`) that represent tasks to create
- Extract the **bolded text** at the start of each item as the basis for the issue title
- Use the rest of the text as the issue description

### Step 2 — Plan before creating

**Always present a plan before creating issues:**

- Show a table with: proposed title, description summary
- Wait for user approval before proceeding
- Allow user to adjust titles or skip items

Example format:

```
| # | Proposed Title | Description (Summary) |
|---|----------------|----------------------|
| 1 | Fix login bug | Users can't log in when... |
| 2 | Add dark mode | Support dark mode toggle in settings... |
```

### Step 3 — Improve titles when needed

When converting checkbox items to issue titles:

- If the item has **bolded text** at the start, use that as the title basis
- If no bold text exists, create a clear, actionable title from the content
- Titles should be:
  - Imperative or descriptive (e.g., "Fix X", "Add Y", "X is broken")
  - Concise but specific (avoid vague titles like "Bug fix")
  - Sentence case (capitalize first word only)

### Step 4 — Format descriptions

Issue descriptions should include:

- **Current behavior** (if it's a bug)
- **Expected behavior**
- **Implementation notes** (if provided in source)
- **References/links** (if any URLs are mentioned)

Use markdown formatting (bold, lists, code blocks) for clarity.

### Step 5 — Create issues in batches

- Use `user-linear-create_issue` for each issue
- Required fields: `title`, `team`, and optionally `project`
- Call multiple create operations in parallel when possible (batch 5-6 at a time)
- Collect all created issue IDs and URLs

### Step 6 — Report results

After creation, provide a summary table:

```
| Issue | Title | Link |
|-------|-------|------|
| ARD-101 | Fix login bug | [View](https://linear.app/...) |
```

## Common Linear MCP operations

### Finding teams and projects

```
user-linear-list_teams          # Get all teams
user-linear-list_projects       # Get all projects (optionally filter by team)
user-linear-get_project         # Get project by name or ID
```

### Creating issues

```
user-linear-create_issue
  - title: string (required)
  - team: string (required) — team name or ID
  - project: string (optional) — project name or ID
  - description: string (optional) — markdown supported
  - priority: number (optional) — 0=None, 1=Urgent, 2=High, 3=Normal, 4=Low
  - labels: string[] (optional) — label names or IDs
  - assignee: string (optional) — user name, email, or "me"
```

### Updating issues

```
user-linear-update_issue
  - id: string (required) — issue ID
  - state: string (optional) — e.g., "canceled", "done", "in progress"
  - (all other fields from create_issue are also available)
```

### Other useful operations

```
user-linear-list_issues         # Search/filter issues
user-linear-get_issue           # Get issue details by ID
user-linear-create_comment      # Add comment to an issue
user-linear-list_issue_labels   # Get available labels
user-linear-list_issue_statuses # Get available statuses for a team
```

## Notes

- Linear MCP cannot permanently delete issues — use `state: "canceled"` to archive
- Issues are created in "Backlog" status by default
- Each issue gets an auto-generated git branch name (e.g., `tim/ard-123-fix-bug`)
- The MCP connection may occasionally fail — retry or restart Cursor if needed
