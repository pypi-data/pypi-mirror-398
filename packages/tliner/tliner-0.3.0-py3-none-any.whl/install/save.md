---
description: "Save findings/outcomes into a Timeline"
allowed_tools: ["Read", "Write", "Edit", "Glob", "LS", "mcp__timeliner__task_create", "mcp__timeliner__save_step", "mcp__timeliner__show_task"]
---

# Task
Execute the save operation according to the next rules.

$ARGUMENTS

## Flow
0. **MANDATORY GOLDEN RULE**: Write like you're explaining to a colleague in Slack. Short sentences. Simple words.  Lazy and direct. Casual BUT keep full technical precision: exact commands, complete file paths, detailed stack traces.
   - ✅ Good Format: "Tried X. Got Y. Fixed Z in file"
   - ✅ GOOD: "Tried `/api/user` endpoint. Got 404. Fixed route in `src/routes.py#L42`."
   - ✅ GOOD: "Parser crashed on `test.json`. Missing null check in `lexer.cpp#L289`. Added guard."
   - ❌ BAD: "An investigation was conducted regarding the API endpoint configuration, which revealed that the routing mechanism was not properly configured to handle user-related requests."
1.  **Generate Content**:
    *   Carefully enumerate what you know so far    
    *   Generate the outcomes for the current step following the "Content Structure" and "Rules".
2.  **Self-Review** (MANDATORY before saving):
    *   Scan your content for robotic patterns. If found - rewrite:
        *   ❌ Avoid Passive voice: "was conducted", "was configured", "was modified", "was determined"
        *   ❌ Avoid Corporate speak: "regarding", "mechanism", "proper", "related", "utilize", "facilitate", "orchestration"
        *   ❌ Avoid Abstract nouns: "investigation", "implementation", "configuration", "verification"
        *   ✅ Use: Active verbs, "I/we" pronouns, short sentences (max 15 words), keep all technical details
3.  **Save to Timeliner**:
    *   Call `mcp__timeliner__save_step` with the following parameters:
        *   `task_id`: Use the memorized `task_id` if you have one. If this is the first time saving for this task, send an **empty string** (`""`). The system will create a new task and return the new `task_id`.
        *   `title`: Up to 5 words which represent essence of the step.
        *   `outcomes`: The exact content that you just generated.
    *   **VERY IMPORTANT**: If a new `task_id` is returned, you MUST memorize it for all future `save_step` calls for this task.
    
## Content Structure

1. **Summary**: Describe current step summary and general flow of investigation.
2. **User Input**: Note ALL user's input and direction they want to go.
3. **Facts**: Main goal is describing outcomes as facts with GREAT details (not only summary).
   - ✅ GOOD: "Rebuilt kernel with `CONFIG_DEBUG_INFO=y`. Boot time dropped from 8.2s to 3.1s. Traced delay to initramfs decompression in `init/initramfs.c#L647`."
   - ❌ BAD: "The kernel configuration was modified to enable debugging information. Performance improvements were observed during the boot sequence. Analysis revealed that initialization delays were attributable to decompression operations."
4. **Resources**: Note ALL resources used (files, links, tools, commands, etc) with direct links (full path/URL/command).
5. **Lessons Learned**: *Avoid to add this section in MOST cases*, except:
    - **Use for**: User-insisted memories ("NEVER", "ALWAYS", "MEMORIZE").
    - **NEVER for:** Task-specific observations, general outcomes, history, what you did in this step.
    - **Format**: Short fundamental rules. Up to 10 items (max 200 characters each).
   - ✅ GOOD: "Run `make clean` before changing kernel configs. Incremental builds cache old flags."
   - ❌ BAD: "It was determined that comprehensive build cleanup procedures should be executed prior to modification of configuration parameters, as incremental compilation processes maintain cached state from previous builds."
   

## Rules
1. **Title**: The `outcomes` content MUST NOT include the title. The title is passed as a separate `title` parameter to the tool.
2. **Content Headings**: All main sections within the `outcomes` (e.g., Summary, Facts, User Input) MUST start with a level 2 heading (`##`). Do NOT use level 1 headings.
3. **Avoids**: NO conclusions, NO hypothesis, NO proposals, NO assumptions, NO speculations, NO generalizations.
4. **Terminology**: Do not use "final", "real solution", "ultimate", "perfect", "best", "ideal", "correct" - use "current" instead. We are documenting current state of investigation, not final solution.
5. **Evidence**: Including evidences for statements is mandatory:
    - Link to source files with line numbers: `[cmd line flags](../src/go/flags.go#L94)`
    - Links to external resources: `[config docs](https://example.com/docs/setup.html)`
6. **Structure**: 
    - Fit all outcomes in ONE chapter, don't split into several chapters.
    - Feel free to use multiple sub-sections inside the step chapter.
7. **Visualisation**:  Prefer to use of diagrams/tables above the long explanations.
