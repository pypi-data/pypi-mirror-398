"""
MkDocs hook to customize navigation titles with timestamp prefix from front-matter.
Formats navigation as: "YY_MM_DD-HH - Title"
Also strips visible front-matter metadata blocks from page content.
"""

import builtins
import contextlib
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_DETECTED_EDITORS: list[tuple[str, str]] | None = None

EDITOR_PROTOCOLS = {
    "vscode": ("📝 VSCode", ["code-url-handler.desktop", "code.desktop"], ["Visual Studio Code.app"]),
    "cursor": ("📝 Cursor", ["cursor-url-handler.desktop", "cursor.desktop"], ["Cursor.app"]),
    "zed": ("📝 Zed", ["dev.zed.Zed.desktop", "zed.desktop"], ["Zed.app"]),
    "code-insiders": ("📝 Insiders", ["code-insiders-url-handler.desktop"], ["Visual Studio Code - Insiders.app"]),
    "sublime": ("📝 Sublime", ["sublime-url-handler.desktop", "sublime_text.desktop"], ["Sublime Text.app"]),
    "idea": ("💡 IntelliJ", ["jetbrains-idea.desktop", "idea.desktop"], ["IntelliJ IDEA.app"]),
    "pycharm": ("🐍 PyCharm", ["jetbrains-pycharm.desktop", "pycharm.desktop"], ["PyCharm.app"]),
    "webstorm": ("💎 WebStorm", ["jetbrains-webstorm.desktop", "webstorm.desktop"], ["WebStorm.app"]),
    "phpstorm": ("🐘 PhpStorm", ["jetbrains-phpstorm.desktop", "phpstorm.desktop"], ["PhpStorm.app"]),
    "clion": ("🔧 CLion", ["jetbrains-clion.desktop", "clion.desktop"], ["CLion.app"]),
    "goland": ("🐹 GoLand", ["jetbrains-goland.desktop", "goland.desktop"], ["GoLand.app"]),
    "rustrover": ("🦀 RustRover", ["jetbrains-rustrover.desktop", "rustrover.desktop"], ["RustRover.app"]),
    "rider": ("🎮 Rider", ["jetbrains-rider.desktop", "rider.desktop"], ["Rider.app"]),
    "atom": ("⚛️ Atom", ["atom-url-handler.desktop", "atom.desktop"], ["Atom.app"]),
    "nova": ("⭐ Nova", ["nova.desktop"], ["Nova.app"]),
    "bbedit": ("📝 BBEdit", ["bbedit.desktop"], ["BBEdit.app"]),
    "textmate": ("📝 TextMate", ["textmate.desktop"], ["TextMate.app"]),
    "emacs": ("📋 Emacs", ["emacs.desktop", "emacsclient.desktop"], ["Emacs.app"]),
    "vim": ("✏️ Vim", ["vim.desktop", "gvim.desktop"], ["MacVim.app"]),
    "neovim": ("✏️ Neovim", ["nvim.desktop", "neovide.desktop"], ["Neovim.app"]),
}


def detect_editors_windows() -> list[tuple[str, str]]:
    try:
        import winreg  # noqa: PLC0415
    except ImportError:
        return []

    found: list[tuple[str, str]] = []
    max_editors = 5
    for protocol, (label, _, _) in EDITOR_PROTOCOLS.items():
        try:
            key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, protocol)
            winreg.CloseKey(key)
            found.append((protocol, label))
            if len(found) >= max_editors:
                break
        except OSError:
            pass
    return found


def detect_editors_macos() -> list[tuple[str, str]]:
    try:
        import plistlib  # noqa: PLC0415, F401
    except ImportError:
        return []

    app_dirs = [Path("/Applications"), Path.home() / "Applications"]

    app_bundles: set[str] = set()
    for app_dir in app_dirs:
        if app_dir.exists():
            with contextlib.suppress(builtins.BaseException):
                app_bundles.update(f.name for f in app_dir.glob("*.app"))

    found: list[tuple[str, str]] = []
    max_editors = 5
    for protocol, (label, _, macos_apps) in EDITOR_PROTOCOLS.items():
        for app_name in macos_apps:
            if app_name in app_bundles:
                found.append((protocol, label))
                break
        if len(found) >= max_editors:
            break

    return found


def detect_editors_linux() -> list[tuple[str, str]]:
    app_dirs = [Path.home() / ".local/share/applications", Path("/usr/share/applications"), Path("/usr/local/share/applications")]

    desktop_files: set[str] = set()
    for app_dir in app_dirs:
        if app_dir.exists():
            with contextlib.suppress(builtins.BaseException):
                desktop_files.update(f.name for f in app_dir.glob("*.desktop"))

    found: list[tuple[str, str]] = []
    max_editors = 5
    for protocol, (label, desktop_patterns, _) in EDITOR_PROTOCOLS.items():
        for pattern in desktop_patterns:
            if pattern in desktop_files:
                found.append((protocol, label))
                break
        if len(found) >= max_editors:
            break

    return found


def detect_installed_editors() -> list[tuple[str, str]]:
    global _DETECTED_EDITORS  # noqa: PLW0603
    if _DETECTED_EDITORS is not None:
        return _DETECTED_EDITORS

    if sys.platform == "win32":
        _DETECTED_EDITORS = detect_editors_windows()
    elif sys.platform == "darwin":
        _DETECTED_EDITORS = detect_editors_macos()
    else:
        _DETECTED_EDITORS = detect_editors_linux()

    return _DETECTED_EDITORS


def generate_editor_buttons(abs_path: Path) -> str:
    editors = detect_installed_editors()
    buttons: list[str] = []

    for protocol, label in editors:
        buttons.append(f'<a href="{protocol}://file{abs_path}" style="margin-right: 10px;">{label}</a>')

    return "".join(buttons)


def on_page_markdown(markdown: str, page: Any, config: dict[str, Any], files: Any) -> str:
    """
    Hook that processes markdown before rendering.
    Removes visible front-matter metadata blocks from content.
    Adds link to open source file in editor at the top.
    """
    source_path = Path(config["docs_dir"]) / page.file.src_path
    abs_path = source_path.absolute()

    editor_buttons = generate_editor_buttons(abs_path)

    task_id_display = ""
    if page.meta and "timestamp" in page.meta:
        task_id = page.meta["timestamp"]
        copy_script = f"navigator.clipboard.writeText('{task_id} '); this.textContent='✓ Copied!'; setTimeout(() => this.textContent='🆔 {task_id}', 1500); return false;"
        task_id_display = f"""<div><a href="#" onclick="{copy_script}"> 🆔 {task_id}</a></div>"""

    copy_path_script = f"navigator.clipboard.writeText('{abs_path}'); this.textContent='✓ Copied!'; setTimeout(() => this.textContent='📋 Copy path ', 1500); return false;"
    edit_link = f"""<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1em; font-size: 0.9em;">
<div>{task_id_display}</div>
<div><a href="#" onclick="{copy_path_script}">📋 Copy path </a>{editor_buttons}</div>
</div>

"""

    pattern = r"^(# Step[^\n]*)\n\s*---\s*\n.*?\n---\s*\n?"
    cleaned = re.sub(pattern, r"\1\n\n", markdown, flags=re.MULTILINE | re.DOTALL)
    cleaned = re.sub(r"^timestamp:\s+\S+\s+tags:\s+\S+\s+metadata:\s+\S+\s*$", "", cleaned, flags=re.MULTILINE)

    return edit_link + cleaned


def on_page_context(context: dict[str, Any], page: Any, config: dict[str, Any], nav: Any) -> dict[str, Any]:
    """
    Hook that runs after page content is loaded.
    Extracts timestamp from front-matter and prepends to nav title.
    """
    if page.meta and "timestamp" in page.meta:
        timestamp = page.meta["timestamp"]

        if isinstance(timestamp, str):
            try:
                dt = datetime.strptime(timestamp, "%Y%m%dT%H%M%S.%fZ").replace(tzinfo=UTC)
                timestamp_clean = dt.strftime("%y.%m.%d-%H")
                title = page.meta.get("title", page.title)
                page.title = f"{timestamp_clean} - {title}"
            except (ValueError, Exception):  # noqa: BLE001,S110
                pass

    return context


def on_nav(nav: Any, config: dict[str, Any], files: Any) -> Any:  # noqa: C901
    """
    Hook that runs after navigation is constructed.
    Updates navigation item titles with timestamp prefix.
    """

    def update_nav_items(items: Any) -> None:
        if not items:
            return
        for item in items:
            if hasattr(item, "children") and item.children:
                update_nav_items(item.children)
            elif hasattr(item, "file") and item.file:
                file_path = Path(config["docs_dir"]) / item.file.src_path
                if not file_path.exists():
                    continue

                content = file_path.read_text(encoding="utf-8")
                match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
                if not match:
                    continue

                front_matter = match.group(1)
                timestamp_match = re.search(r"timestamp:\s*([^\n]+)", front_matter)
                if not timestamp_match:
                    continue

                timestamp = timestamp_match.group(1).strip()
                try:
                    dt = datetime.strptime(timestamp, "%Y%m%dT%H%M%S.%fZ").replace(tzinfo=UTC)
                    timestamp_clean = dt.strftime("%y.%m.%d-%H")

                    title_match = re.search(r"title:\s*([^\n]+)", front_matter)
                    title = title_match.group(1).strip() if title_match else item.title

                    item.title = f"{timestamp_clean} - {title}"
                except (ValueError, Exception):  # noqa: BLE001,S110
                    pass

    if nav:
        update_nav_items(nav.items)

    return nav
