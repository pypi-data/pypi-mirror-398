from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from .mkdocs_builder import initialize_mkdocs, shutdown_mkdocs
from .models import Step
from .services import Timeline
from .utils0 import L as logger  # noqa: N811

DEFAULT_MAX_CHARS = 60000
MIN_MAX_CHARS = 1000
DEFAULT_MAX_TOKENS = DEFAULT_MAX_CHARS // 4
MIN_MAX_TOKENS = MIN_MAX_CHARS // 4

TRUNCATION_SUFFIX = " [...truncated]"


def paginate_steps(steps: list[Step], max_chars: int = DEFAULT_MAX_CHARS) -> list[list[Step]]:
    max_chars = max(max_chars, MIN_MAX_CHARS)

    pages: list[list[Step]] = []
    current_page: list[Step] = []
    current_chars = 0

    for step in steps:
        text = f"{step.title} {step.outcomes}"
        current_step = step

        if len(text) > max_chars:
            max_outcomes = max(0, max_chars - len(step.title) - 1 - len(TRUNCATION_SUFFIX))
            current_step = step.model_copy(update={"outcomes": step.outcomes[:max_outcomes] + TRUNCATION_SUFFIX})
            text = f"{current_step.title} {current_step.outcomes}"

        if current_chars + len(text) > max_chars and current_page:
            pages.append(current_page)
            current_page = []
            current_chars = 0

        current_page.append(current_step)
        current_chars += len(text)

    if current_page:
        pages.append(current_page)

    return pages or [[]]


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[None]:  # noqa: ARG001
    logger.info("FastMCP lifespan starting...")

    # Initialize MkDocs
    await initialize_mkdocs()

    try:
        yield
    finally:
        # Cleanup
        logger.info("FastMCP lifespan shutting down...")
        shutdown_mkdocs()


app = FastMCP("timeliner", lifespan=app_lifespan)
service = Timeline()


@app.tool()
def task_list() -> dict:
    """
    Lists all tasks in the system.

    WHEN TO USE:
    - To discover existing tasks
    - To find a task_id when you need to add steps to existing work
    - To review what work has been tracked in the Timeline

    Returns: dict containing list of all tasks with their task_id, title, and file paths
    """
    tasks = service.get_all_tasks()
    return {"tasks": [task.model_dump() for task in tasks]}


@app.tool()
def save_step(task_id: str, title: str, outcomes: str, tags: list[str] | None = None, metadata: dict[str, str] | None = None) -> dict:
    """
    Records the step in the Timeline for tracking AI agent work outcomes.

    WHEN TO USE:
    - After completing any significant work (bug fix, feature implementation, investigation)
    - To document decisions, findings, or outcomes that future context might need
    - To create audit trail of what was done and why

    WORKFLOW:
    1. First time? Pass "new" as task_id to auto-create new task (also accepts: "", '""', '"new"')
    2. Subsequent steps? Use the task_id returned from previous save_step call (e.g., "20251208T103349.797731Z")
    3. Add descriptive tags to make steps searchable (e.g., ["bugfix", "authentication"])
    4. Include metadata links to related resources (GitHub issues, PRs, commits)

    Args:
        task_id: Task identifier. To CREATE NEW: use "new". To APPEND: use existing task_id (e.g., "20251208T103349.797731Z")
        title: Concise step description (e.g., "Fixed login timeout bug")
        outcomes: Detailed explanation of what was done, decisions made, and results
        tags: Optional categorization tags ["feature", "refactor", "investigation"]
        metadata: Optional links {"github_issue": "https://...", "pr": "https://...", "commit": "abc123"}

    Returns: dict with task_id, step_id, and file_path to the task's markdown file
    """
    # Check correctness of 'task_id'
    if task_id is None or not isinstance(task_id, str):
        raise ValueError(f"Invalid type of task_id ({task_id}). Please provide a valid task_id type or empty string.")

    # Normalize pseudo-empty strings that LLMs sometimes send
    # Support: "", '""', "new", '"new"' as indicators to create new task
    normalized_task_id = task_id.strip()
    if normalized_task_id in ['""', "new", '"new"', "'new'"]:
        normalized_task_id = ""

    # fetch Task instance and check if task exist
    if not normalized_task_id:
        task = service.create_task(title=title)
        if not task:
            raise ValueError(f"Unable to create task ({task_id}). Failed when at file creating.")  # TODO @vz: what llm should do?
    else:
        task = service.get_task(normalized_task_id)
        if not task:
            raise ValueError(f"Task with id {normalized_task_id} does not exist. Please provide a valid task_id or empty string.")

    # Create step
    step = service.create_step(task.task_id, title, outcomes, tags, metadata)
    if not step:
        raise ValueError("Failed to create the step.")  # TODO @vz: what llm should do?

    logger.info(f"Successfully saved step for task {task_id}")
    return {"task_id": task.task_id, "step_id": step.step_id, "file_path": task.file_path}


@app.tool()
def get_steps(since: str = "", until: str = "", ids: list[str] | None = None, page: int = 1, max_tokens: int = DEFAULT_MAX_TOKENS) -> dict:
    """
    Retrieves steps from the Timeline with optional filtering by time or IDs.

    WHEN TO USE:
    - To load context from previous work sessions
    - To find relevant past decisions or implementations
    - To review what was done recently or on specific tasks

    FILTERING OPTIONS:
    - No filters: Returns ALL steps across all tasks
    - since only: Get steps from a specific time [include] onwards (ISO format: "2025-01-01T00:00:00Z")
    - until only: Get steps up to a specific time [exclude] (ISO format: "2025-02-01T00:00:00Z")
    - since and until: Get steps in a specific time range
    - ids: Get steps by task_id OR step_id (accepts both, auto-detects type)
    - Combine: Mix time and ID filters for precise queries
    - NOTE: Steps and tasks always use the UTC timezone for timestamps. Convert local time to UTC BEFORE providing 'since' and 'until' filters.

    PAGINATION:
    - Results are paginated by token count (uses chars/4 approximation, not real tokenizer)
    - Pages are 1-indexed (first page is page=1)
    - Oversized steps are truncated with "[...truncated]" suffix

    Args:
        since: Optional ISO UTC format timestamp to filter steps from  [include] (e.g., "2025-01-01T00:00:00Z")
        until: Optional ISO UTC format timestamp to filter steps until [exclude] (e.g., "2025-02-01T00:00:00Z")
        ids: Optional list of task IDs or step IDs to filter steps (e.g., ["20251208T103349.797731Z"])
        page: Page number to retrieve, 1-indexed (default: 1)
        max_tokens: Maximum tokens per page, uses chars/4 approximation (default: 15000 tokens, min: 250 tokens)

    Returns: dict with steps array, count, and pagination info (page, total_pages)
    """
    steps = service.get_all_steps(since=since, until=until)

    if ids:
        steps = [m for m in steps if m.task_id in ids or m.step_id in ids]

    max_chars = max_tokens * 4
    pages = paginate_steps(steps, max_chars)
    total_pages = len(pages)

    page = max(1, min(page, total_pages)) if total_pages > 0 else 1
    page_steps = pages[page - 1] if total_pages > 0 else []

    step_dicts = []
    for m in page_steps:
        m_dict = m.model_dump()
        m_dict["timestamp"] = m.timestamp.isoformat()
        step_dicts.append(m_dict)

    return {"steps": step_dicts, "count": len(step_dicts), "pagination": {"page": page, "total_pages": total_pages}}
