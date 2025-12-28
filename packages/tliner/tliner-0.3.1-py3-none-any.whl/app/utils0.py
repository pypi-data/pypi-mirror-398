import sys
from datetime import UTC, datetime

from loguru import logger as L  # noqa: N812

from .config import CONFIG

LOGS_FOLDER = CONFIG.logs_folder
LOGS_FOLDER.mkdir(parents=True, exist_ok=True)

MKDOCS_SERVER_LOG = LOGS_FOLDER / "mkdocs.log"
MCP_LOG_FILE = LOGS_FOLDER / f"mcp-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.log"

L.remove()
L.add(sys.stderr, level="TRACE")
L.add(str(MCP_LOG_FILE), backtrace=True, diagnose=True, level="INFO", rotation="10 MB")

L.info(f"Work folder: {CONFIG.work_folder.resolve()}")


def clear_logs_folder() -> None:
    """Clear all files in logs folder, skipping locked files and current MCP log."""
    if not LOGS_FOLDER.exists():
        return

    for file_path in LOGS_FOLDER.glob("*"):
        if file_path.is_file():
            # Skip our own MCP log file
            if file_path == MCP_LOG_FILE:
                L.debug(f"Skipped own MCP log file: {file_path.name}")
                continue

            try:
                file_path.unlink()
                L.debug(f"Removed log file: {file_path.name}")
            except Exception as e:  # noqa: BLE001
                L.debug(f"Skipped locked log file: {file_path.name} ({e})")
