import os
from dataclasses import dataclass
from pathlib import Path

CONFIG_FOLDER_NAME = ".tliner"


def _detect_work_folder() -> Path:
    env_value = os.environ.get("TIMELINER_WORK_FOLDER", "").strip()
    if env_value:
        return Path(os.path.expandvars(env_value)).resolve()

    cwd = Path.cwd().resolve()

    if (cwd / CONFIG_FOLDER_NAME).exists():
        return cwd

    default = cwd / "docs" / "timeline"
    (default / CONFIG_FOLDER_NAME).mkdir(parents=True, exist_ok=True)
    return default


__wf = _detect_work_folder()


@dataclass
class TimelinerConfig:
    mkdocs: bool
    mkdocs_auto_open: bool
    mkdocs_port: int | None
    mkdocs_idle_timeout: int
    mkdocs_regenerate_settings: bool
    mkdocs_site_name: str | None
    mkdocs_reverse_navigation: bool

    work_folder: Path
    config_folder: Path
    logs_folder: Path


CONFIG = TimelinerConfig(
    mkdocs=False,
    mkdocs_auto_open=True,
    mkdocs_port=None,
    mkdocs_idle_timeout=300,
    mkdocs_regenerate_settings=True,
    mkdocs_site_name=None,
    mkdocs_reverse_navigation=False,
    work_folder=__wf,
    config_folder=__wf / CONFIG_FOLDER_NAME,
    logs_folder=__wf / CONFIG_FOLDER_NAME / "logs",
)
