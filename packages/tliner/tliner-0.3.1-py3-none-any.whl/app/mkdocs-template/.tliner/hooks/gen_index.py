import logging
import os
from datetime import UTC, datetime

import mkdocs_gen_files

log = logging.getLogger("mkdocs")

INDEX_TEMPLATE = """---
title: Welcome to Timeliner
timestamp: {{TIMESTAMP}}
---

!!!tip "Timeliner is running 🎉"
    **Work Folder**: `{{WORK_FOLDER_FULL}}` <br/>
    **Site**: [{{SERVE_URL}}]({{SERVE_URL}})

## What is This?

**Diary for your AI** 🤖 - ***Timeliner*** records your AI agent's journey,<br/>
organizing *tasks*, *decisions*, and *outcomes* into a searchable **timeline**.

This site provides:

- 🔍 **Full-text search** - Find any task or step instantly
- 📅 **Chronological navigation** - Tasks organized by timestamp
- 🎨 **Beautiful rendering** - Code blocks, admonitions, lists with proper rendering


## How to Use
- This documentation site **auto-rebuilds** whenever you save a task file
- Navigation shows timestamps in format: `YY.MM.DD-HH - Task Title`


### File Structure

Your workspace contains:
```
{{WORK_FOLDER_FULL}}
├── YYYY_MM_DD-hhmmss-task-tile.md              # Task markdown files
├── 2020_01_21-143001-implment-timeliner.md     # Task markdown files
└── .tliner/              # Generated documentation
    ├── logs/             # Server and MCP logs
    ├── mkdocs.yml        # Configuration
    └── hooks/            # Navigation formatting
```
---
*Auto-generated on {{TIMESTAMP}}*

"""


def generate_index_md() -> None:
    """Generate index.md from embedded template with dynamic values from env vars"""
    log.info("[GEN_INDEX] on_pre_build called")

    work_folder_full = os.environ.get("TIMELINER_WORK_FOLDER", "")
    server = os.environ.get("TIMELINER_SERVER", "unknown")
    port = os.environ.get("TIMELINER_PORT", "????")
    serve_url = f"http://{server}:{port}"
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")

    content = INDEX_TEMPLATE.replace("{{TIMESTAMP}}", timestamp).replace("{{WORK_FOLDER_FULL}}", work_folder_full).replace("{{SERVE_URL}}", serve_url).replace("{{PORT}}", port)

    log.info(f"[GEN_INDEX] Creating index.md with content length: {len(content)}")
    with mkdocs_gen_files.open("index.md", "w") as f:
        f.write(content)
    log.info("[GEN_INDEX] index.md created successfully")


generate_index_md()
