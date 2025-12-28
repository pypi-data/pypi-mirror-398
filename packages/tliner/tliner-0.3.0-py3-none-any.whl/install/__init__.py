#!/usr/bin/env python3
"""Timeliner installer for Claude Code.

Usage:
    uvx --from tliner tliner-install              # Auto-detects: plugin if Claude available
    uvx --from tliner tliner-install --standalone # Force standalone mode
    uvx --from tliner tliner-install -w custom/path  # Standalone with custom work folder
"""

import argparse
import hashlib
import re
import subprocess
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

try:
    from rich.console import Console
    from rich.prompt import Confirm

    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def print_msg(text: str) -> None:
    """Print with Rich if available, else strip markup and print plain."""
    if HAS_RICH:
        console.print(text)
    else:
        clean = re.sub(r"\[.*?\]", "", text)
        print(clean)  # noqa: T201


def confirm(msg: str, default: bool = False) -> bool:
    """Prompt yes/no with Rich or plain input."""
    if HAS_RICH:
        return Confirm.ask(msg, default=default)

    prompt = f"{msg} [{'Y/n' if default else 'y/N'}]: "
    response = input(prompt).strip().lower()
    if not response:
        return default
    return response in ("y", "yes")


def detect_claude_setup(cwd: Path) -> tuple[bool, str]:
    """Returns (has_setup, reason)."""
    if (cwd / ".claude").is_dir():
        return True, ".claude/ directory exists"
    if (cwd / "CLAUDE.md").is_file():
        return True, "CLAUDE.md file exists"
    return False, "No .claude/ or CLAUDE.md found. Re-run tliner installer from the exisitng Claude project."


def ensure_claude_dir(cwd: Path) -> Path:
    """Create .claude/commands/ if missing."""
    claude_dir = cwd / ".claude"
    claude_dir.mkdir(exist_ok=True)
    commands_dir = claude_dir / "commands"
    commands_dir.mkdir(exist_ok=True)
    return claude_dir


def validate_and_create_work_folder(base_path: Path, work_folder: str) -> Path:
    """Validate work_folder path and create it with .tliner marker."""
    work_path = (base_path / work_folder).resolve()

    if not work_path.is_relative_to(base_path.resolve()):
        print_msg("[red]Invalid work folder: path escapes project directory[/red]")
        raise SystemExit(1)

    work_path.mkdir(parents=True, exist_ok=True)
    (work_path / ".tliner").mkdir(exist_ok=True)

    return work_path


def _build_mcp_add_command(work_folder: str) -> list[str]:
    """Build MCP add command with work folder env var."""
    return ["claude", "mcp", "add", "--scope", "project", "--transport", "stdio", "timeliner", "--env", f"TIMELINER_WORK_FOLDER=${{PWD}}/{work_folder}", "--", "uvx", "tliner@latest", "serve"]


def _run_claude_command(cmd: list[str]) -> tuple[bool, str]:
    """Execute claude CLI command. Returns (success, message)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
        if result.returncode != 0:
            return False, result.stderr
        return True, result.stdout  # noqa: TRY300
    except FileNotFoundError:
        return False, "'claude' CLI not found. Install Claude Code first."


def file_hash(content: str) -> str:
    """Calculate SHA256 hash of string content."""
    return hashlib.sha256(content.encode()).hexdigest()


def backup_file(file_path: Path) -> Path:
    """Create timestamped backup of any file."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.parent / f"{file_path.name}.backup.{timestamp}"
    backup_path.write_text(file_path.read_text())
    return backup_path


def update_mcp_server_safe(work_folder: str) -> tuple[bool, str]:
    """Add or update MCP server. Returns (success, message)."""
    success, msg = _run_claude_command(_build_mcp_add_command(work_folder))

    if success:
        return True, "MCP server configured"

    if "already exists" in msg.lower():
        _run_claude_command(["claude", "mcp", "remove", "--scope", "project", "timeliner"])
        success, msg = _run_claude_command(_build_mcp_add_command(work_folder))
        if not success:
            return False, f"Failed to update MCP server: {msg}"
        return True, "MCP server configured"

    return False, f"Failed to add MCP server: {msg}"


def create_command_file(commands_dir: Path, name: str, template: str) -> tuple[Path, str]:
    """Copy command template to .claude/commands/{name}.md. Returns (path, status)."""
    template_path = Path(__file__).parent / f"{template}.md"

    try:
        template_content = template_path.read_text()
    except FileNotFoundError:
        print_msg(f"[red]Error: Template file '{template}.md' not found in package[/red]")
        raise SystemExit(1) from None

    cmd_file = commands_dir / f"{name}.md"

    if cmd_file.exists():
        existing_content = cmd_file.read_text()
        existing_hash = file_hash(existing_content)
        new_hash = file_hash(template_content)

        if existing_hash == new_hash:
            return cmd_file, "skipped"

        backup_path = backup_file(cmd_file)
        cmd_file.write_text(template_content)
        return cmd_file, f"updated (backup: {backup_path.name})"

    cmd_file.write_text(template_content)
    return cmd_file, "created"


MARKETPLACE_GITHUB = "sinai-io/ai-plugins"
MARKETPLACE_NAME = "sinai-io"


def _is_marketplace_installed(name: str) -> bool:
    """Check if marketplace is already installed."""
    success, output = _run_claude_command(["claude", "plugin", "marketplace", "list"])
    if not success:
        return False
    return name in output


def run_install_plugin() -> int:
    """Install timeliner as Claude Code plugin from GitHub marketplace. Returns exit code."""
    cwd = Path.cwd()

    try:
        pkg_version = version("tliner")
    except Exception:  # noqa: BLE001
        pkg_version = "unknown"

    print_msg(f"[bold cyan]Timeliner Plugin Installation (v{pkg_version})[/bold cyan]\n")

    print_msg("[cyan]Checking marketplace...[/cyan]")
    if _is_marketplace_installed(MARKETPLACE_NAME):
        print_msg(f"[green]✓[/green] Marketplace: {MARKETPLACE_GITHUB} (already installed)")
    else:
        success, msg = _run_claude_command(["claude", "plugin", "marketplace", "add", MARKETPLACE_GITHUB])
        if not success:
            print_msg(f"[red]✗[/red] Failed to add marketplace: {msg}")
            return 1
        print_msg(f"[green]✓[/green] Marketplace: {MARKETPLACE_GITHUB}")

    ensure_claude_dir(cwd)
    print_msg("\n[cyan]Installing plugin (project scope)...[/cyan]")
    success, msg = _run_claude_command(["claude", "plugin", "install", "tliner", "--scope", "project"])
    if not success:
        print_msg(f"[red]✗[/red] Plugin install failed: {msg}")
        print_msg(f"[dim]Error: {msg}[/dim]")
        return 1
    print_msg("[green]✓[/green] Plugin installed")

    print_msg("\n[bold green]Plugin installation complete![/bold green]")
    print_msg("[cyan]Summary:[/cyan]")
    print_msg(f"  • Marketplace: {MARKETPLACE_GITHUB}")
    print_msg("  • Plugin: tliner (project scope)")
    print_msg("  • Commands: /tliner:save, /tliner:load, /tliner:report")
    print_msg("  • MCP server: timeliner (bundled)")
    env_exmpl = '"env": {"TIMELINER_WORK_FOLDER": "${PWD}/info/mydocs"}'
    print_msg(f"\n[yellow]Note:[/yellow] To customize work folder set TIMELINER_WORK_FOLDER in .claude/settings.json: {env_exmpl}")
    print_msg("[dim]Default: docs/timeline (relative to project)[/dim]")
    print_msg(f"\n[dim]Project: {cwd}[/dim]")

    return 0


def run_install_claude(work_folder: str) -> int:  # noqa: C901, PLR0912
    """Main installation logic (standalone mode). Returns exit code."""
    cwd = Path.cwd()

    try:
        pkg_version = version("tliner")
    except Exception:  # noqa: BLE001
        pkg_version = "unknown"

    print_msg(f"[bold cyan]Timeliner Installation (v{pkg_version})[/bold cyan]\n")

    has_setup, reason = detect_claude_setup(cwd)
    if has_setup:
        print_msg(f"[green]✓[/green] Claude setup detected: {reason}")
    else:
        print_msg(f"[yellow]⚠[/yellow] {reason}")
        if not confirm("Create .claude/ directory?", default=True):
            print_msg("[red]Installation cancelled.[/red]")
            return 1

    claude_dir = ensure_claude_dir(cwd)
    print_msg(f"[green]✓[/green] Directory ready: {claude_dir}")

    work_path = validate_and_create_work_folder(cwd, work_folder)
    print_msg(f"[green]✓[/green] Work folder created: {work_path}")

    mcp_config = cwd / ".mcp.json"
    mcp_backup_created = False
    if mcp_config.exists():
        backup_path = backup_file(mcp_config)
        mcp_backup_created = backup_path.name

    print_msg(f"\n[cyan]Configuring MCP server (work folder: {work_folder})...[/cyan]")
    mcp_success, mcp_message = update_mcp_server_safe(work_folder)
    if not mcp_success:
        print_msg(f"[red]✗[/red] MCP server failed: {mcp_message}")
        print_msg("[red]Installation stopped. Fix MCP server issue and retry.[/red]")
        return 1
    print_msg(f"[green]✓[/green] {mcp_message}")

    commands_dir = claude_dir / "commands"
    cmd_results = {}

    for cmd_name, template_name in [("save", "save"), ("load", "load"), ("report", "report")]:
        _cmd_file, status = create_command_file(commands_dir, cmd_name, template_name)
        cmd_results[cmd_name] = status
        if status == "skipped":
            print_msg(f"[dim]○[/dim] /{cmd_name} unchanged (identical)")
        elif "updated" in status:
            print_msg(f"[green]✓[/green] /{cmd_name} {status}")
        else:
            print_msg(f"[green]✓[/green] /{cmd_name} {status}")

    print_msg("\n[bold green]Installation complete![/bold green]")
    print_msg("[cyan]Summary:[/cyan]")
    if mcp_backup_created:
        print_msg(f"  • MCP Server: {mcp_message} (backup: {mcp_backup_created})")
    else:
        print_msg(f"  • MCP Server: {mcp_message}")

    cmd_summary = []
    for cmd_name, status in cmd_results.items():
        cmd_summary.append(f"/{cmd_name} ({status})")
    print_msg(f"  • Commands: {', '.join(cmd_summary)}")

    print_msg(f"\n[dim]Work folder: {cwd / work_folder}[/dim]")

    return 0


def _is_claude_available() -> bool:
    """Check if Claude CLI is available."""
    success, _ = _run_claude_command(["claude", "--version"])
    return success


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description="Install timeliner into Claude Code project")
    parser.add_argument("--work-folder", "-w", help="Work folder for timeline storage (forces standalone mode)")
    parser.add_argument("--standalone", action="store_true", help="Force standalone installation (copy commands to .claude/)")
    parser.add_argument("--as-plugin", action="store_true", help="Force plugin installation")
    args = parser.parse_args(argv)

    if args.standalone or args.work_folder:
        return run_install_claude(args.work_folder or "docs/timeline")

    if args.as_plugin or _is_claude_available():
        return run_install_plugin()

    return run_install_claude(args.work_folder or "docs/timeline")


if __name__ == "__main__":
    sys.exit(main())
