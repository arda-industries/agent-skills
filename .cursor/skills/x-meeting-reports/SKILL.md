---
name: x-meeting-reports
description: Create meeting report entries in the Notion meeting reports database. Use when the user asks to create a meeting report, log a meeting, or add a meeting to Notion. Requires Notion MCP.
---

# Meeting Reports (Notion)

Create new meeting report entries in the user's Notion meeting reports database. **Notion MCP must be available.** If you cannot call Notion MCP tools (e.g. `notion-fetch`, `notion-create-pages`), stop and reply: **"Creating meeting reports requires the Notion MCP to be available. Please enable the Notion MCP in Cursor and try again."**

## Target database

- **URL:** https://www.notion.so/d30ba60af8344e99b97a94428f838ccb?v=fbe020906b5c4f98a1b792d87883f76f
- New reports are created as **child pages of this database** (one new row per report).

## Workflow (strict order)

1. **User describes the meeting** (paste notes, bullet points, or describe verbally).
2. **You propose the full Notion update:** Draft the exact **title**, **type** (Internal vs External), **database properties** (e.g. Date, People, Status), and **page body** (sections and content) you would create. Present this in one clear block (e.g. markdown) for approval.
3. **User approves** (or requests edits).
4. **You create the page:** Use Notion MCP to create the page in the database with the approved content. Confirm with the link to the new page.

Do **not** create or update anything in Notion until the user has explicitly approved the proposal.

## Report types

| Type       | When to use | Example |
|-----------|-------------|---------|
| **Internal** | Call debriefs, internal syncs, team meetings | [Eagleeye call debrief](https://www.notion.so/Eagleeye-call-debrief-2fd4d59545c280c8be3bccb12c3f0cd8) |
| **External** | Meetings with external contacts (customers, partners, prospects) | [Maegan Eagleye](https://www.notion.so/Maegan-Eagleye-2fc4d59545c28020bd30dd32f9ebc218) |

## Matching existing structure

Before creating a report (or when property names / layout are unclear):

1. **Fetch the database** with `notion-fetch` using the database URL above to see property names and types.
2. **Fetch one or both example pages** with `notion-fetch`:
   - Internal: `https://www.notion.so/Eagleeye-call-debrief-2fd4d59545c280c8be3bccb12c3f0cd8`
   - External: `https://www.notion.so/Maegan-Eagleye-2fc4d59545c28020bd30dd32f9ebc218`
3. Reuse the **same property names**, **section headings**, and **content style** (bullets, short paragraphs) so new reports look consistent.

## Attendees

When the user provides them, include:
- **Internal attendees** (your team)
- **External attendees** (contacts/customers)

Add these to database properties (e.g. People, Attendees) if the schema has them, and/or in the page body under an **Attendees** section (Internal: … / External: …).

## Creating the page

- Use **notion-create-pages** (or the equivalent Notion MCP create tool) with:
  - **Parent:** the meeting reports database (use the database URL or ID as the parent).
  - **Properties:** all required and relevant database properties (e.g. Name/Title, Date, Type, People, Status), matching the schema you fetched.
  - **Content:** the approved body (summary, key points, action items, follow-ups) in the same structure as the examples.

If the MCP expects markdown or blocks, format the body to match the example pages (headings, bullet lists, callouts as used there).

## Creating in database (workaround)

If **notion-create-pages** fails because the `parent` parameter is received as a string (MCP serialization), create the report **inside the database** by:

1. **Duplicating** an existing report that is already a row in the database (e.g. [Maegan Eagleye](https://www.notion.so/Maegan-Eagleye-2fc4d59545c28020bd30dd32f9ebc218)) using **notion-duplicate-page**. The new page will be a new row in the same database.
2. **Updating** the duplicate: use **notion-update-page** to set properties (Title, Date, BLUF, External attendees, Action items, etc.) and replace the page content with the approved body.
3. If **notion-update-page** fails (e.g. `data` received as string), give the user the link to the new duplicate and short manual steps to set the title, date, properties, and paste the body in Notion.

## Summary

- **Requirement:** Notion MCP enabled; otherwise fail with the message above.
- **New chat:** If Notion MCP was enabled after this conversation started, start a new Cursor chat and ask again with the meeting content—the new session will have access to Notion tools.
- **Create new only:** If the user asked to **create** a new meeting report, always create a new page. Do not update an existing report.
- **Flow:** Describe → Propose (title, type, properties, body) → User approves → Create in database.
- **Consistency:** Fetch database + example pages and mirror their structure and property names.
