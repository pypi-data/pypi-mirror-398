---
description: "Your progress summary. Usage: /report [IDs] [since] [until] <topic>"
allowed_tools: ["Read", "mcp__timeliner__get_steps", "mcp__timeliner__task_list"]
---

# Task

Generate a formatted summary of work done on a specific topic by analyzing Task Data in the Timeline.

> **Note**: This command uses the same time parsing and keyword filtering logic as `/load` (see `load.md`).
> execute `/load` then add formatting and grouping on top per the next rules.


### 1. Execute `/load` (`load.md`)

- read `load.md` file and execute it with the  $ARGUMENTS

### 2. Analyze and Group Steps

Group by temporal proximity (1-2 days) and thematic similarity. Each group = one "Approach" section (aim for 2-5).

Extract per approach:
- Main activities (from outcomes)
- Implementation details (files, functions, algorithms)
- Results/status (completed, in progress, blocked)
- Metadata (PR links, commits, issues)

### 3. Generate Report

0. **MANDATORY GOLDEN RULE**: Write like you're explaining to a colleague in Slack. 
   - Short sentences. Simple words.  Lazy and direct. 
   - Casual BUT keep full technical precision: exact commands, complete file paths, detailed stack traces.
   - Examples:
      - ✅ Good Format: "Tried X. Got Y. Fixed Z in file"
	  - ✅ GOOD: "Tried `/api/user` endpoint. Got 404. Fixed route in `src/routes.py#L42`."
	  - ✅ GOOD: "Parser crashed on `test.json`. Missing null check in `lexer.cpp#L289`. Added guard."
	  - ❌ BAD: "An investigation was conducted regarding the API endpoint configuration, which revealed that the routing mechanism was not properly configured to handle user-related requests."

**Format:**
```markdown
# Report: [Topic Name]
**Time period:** [parsed time period or "All time"]
**Generated:** [current UTC timestamp]

---

## Approach 1: [Descriptive Name]

- [Key activity 1 with brief implementation detail]
- [Key activity 2 with brief implementation detail]
- [Key activity 3 with brief implementation detail]
- [Result/outcome achieved]

**Status:** [Completed/In progress/Blocked]

---

## Approach 2: [Descriptive Name]

...

---
```

**Writing style:**
- 3-5 bullets per approach, past tense
- Include technical details (files, algorithms) but stay concise
- No code blocks or function signatures
- 1-2 sentences per bullet
- Final bullet = result/outcome
- Status: Completed, In progress, or Blocked

### 4. Output Report

Print the fully formatted markdown report to terminal for user review.


## Edge Cases and Notes

- **No matches**: Print "No work found for [topic] in period" and exit
- **Single step**: Create one approach section
- **Missing metadata**: Omit if not present
- **Ambiguous time format**: Ask user to clarify
- **Calendar week**: "last week" always refers to previous Monday-Sunday period
- **Exclusive end date**: `until` parameter excludes the boundary (steps < until, not <=)
  - To include a full day: set `until` to next day's midnight
  - Example: "on Oct 28" = since: "2025-10-28T00:00:00Z", until: "2025-10-29T00:00:00Z"
- Keywords for searching must be case-insensitive
- Single date parameter allowed (backend filters with open conditionals)
