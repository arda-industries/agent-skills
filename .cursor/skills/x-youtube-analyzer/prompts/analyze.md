Analyze this YouTube video and provide a structured analysis.

## Required Output Format

Respond with EXACTLY this format (the parser depends on these section headers):

---
TITLE: <the video's title>

CHANNEL: <channel name if visible>

SUMMARY:
<2-3 paragraph summary of the main content, key arguments, and conclusions>

KEY_POINTS:
- [MM:SS] <key point or insight>
- [MM:SS] <key point or insight>
- [MM:SS] <key point or insight>
(provide 5-10 key points with timestamps)

STATIC_MOMENTS:
- [MM:SS] <description of static visual worth capturing as a screenshot>
- [MM:SS] <description of static visual>
(provide 2-5 timestamps for STATIC content: diagrams, slides, code snippets, charts, text on screen, architecture drawings)

DYNAMIC_MOMENTS:
- [MM:SS] (Xs) <description of dynamic content worth capturing as a short clip>
- [MM:SS] (Xs) <description of dynamic content>
(provide 1-3 timestamps for DYNAMIC content that benefits from motion: demonstrations, animations, UI interactions, before/after transitions, physical processes. Include suggested duration in seconds, 1-5s.)
---

## Guidelines

- Use MM:SS format for all timestamps (e.g., 02:30, 15:45)
- For KEY_POINTS, focus on the most important insights, not every topic mentioned
- For STATIC_MOMENTS, identify content where a single frame captures the information:
  - Diagrams and flowcharts
  - Code examples or terminal output
  - Slides with text or data
  - Architecture drawings
  - Charts and graphs
- For DYNAMIC_MOMENTS, identify content where motion is essential to understanding:
  - Software demonstrations (clicking through UI, drag-and-drop)
  - Physical processes or assembly steps
  - Animations explaining concepts
  - Before/after comparisons with transitions
  - Gestures or pointing to explain spatial relationships
- Keep dynamic clips short (1-5 seconds) - just enough to capture the action
- If unsure whether something is static or dynamic, prefer static (screenshots are smaller)
