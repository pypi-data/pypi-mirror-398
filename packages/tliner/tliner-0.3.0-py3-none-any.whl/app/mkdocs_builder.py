import asyncio
import hashlib
import os
import shutil
import socket
import time
import webbrowser
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

import aiohttp

from .config import CONFIG, CONFIG_FOLDER_NAME
from .utils0 import MKDOCS_SERVER_LOG, clear_logs_folder
from .utils0 import L as logger  # noqa: N811


async def fetch_json(url: str, timeout: float = 2.0) -> dict:  # noqa: ASYNC109
    http_ok = 200
    try:
        async with aiohttp.ClientSession() as session, session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
            if response.status == http_ok:
                return await response.json()
            raise RuntimeError(f"HTTP {response.status}") from None  # noqa: TRY301
    except Exception as e:
        raise RuntimeError(f"Failed to fetch {url}: {e}") from e


async def post_json(url: str, data: dict, timeout: float = 2.0) -> dict:  # noqa: ASYNC109
    http_ok = 200
    try:
        async with aiohttp.ClientSession() as session, session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
            if response.status == http_ok:
                return await response.json()
            raise RuntimeError(f"HTTP {response.status}") from None  # noqa: TRY301
    except Exception as e:
        raise RuntimeError(f"Failed to post {url}: {e}") from e


def calculate_stable_port(work_folder: Path) -> int:
    folder_path = str(work_folder.resolve())
    hash_digest = hashlib.md5(folder_path.encode()).hexdigest()  # noqa: S324
    port_offset = int(hash_digest[:8], 16) % 1000
    return 8000 + port_offset


async def check_existing_server(work_folder: Path = CONFIG.work_folder) -> tuple[bool, str | None]:
    work_folder = work_folder.resolve()
    docs_url_file = work_folder / "docs.url"

    if docs_url_file.exists():
        try:
            docs_url = docs_url_file.read_text().strip()
            logger.debug(f"Found docs.url: {docs_url}")

            metadata = await fetch_json(f"{docs_url}/timeliner/metadata")
            server_workfolder = Path(metadata["work_folder"]).resolve()

            if server_workfolder == work_folder:
                logger.info(f"Existing server found via docs.url: {docs_url}")
                return True, docs_url
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Stale docs.url file detected (server unreachable): {e}")
            docs_url_file.unlink(missing_ok=True)
            logger.info("Deleted stale docs.url file")

    main_port = calculate_stable_port(work_folder)
    main_url = f"http://localhost:{main_port}"

    try:
        logger.debug(f"Checking main port {main_port}...")
        metadata = await fetch_json(f"{main_url}/timeliner/metadata")
        server_workfolder = Path(metadata["work_folder"]).resolve()

        if server_workfolder == work_folder:
            logger.info(f"Existing server found via main port: {main_url}")
            docs_url_file.parent.mkdir(parents=True, exist_ok=True)
            docs_url_file.write_text(main_url)
            desktop_file = work_folder / "docs.desktop"
            desktop_file.write_text(f"[Desktop Entry]\nType=Link\nURL={main_url}\nIcon=text-html\n")
            desktop_file.chmod(0o755)
            logger.info("Created docs.url file for discovered server")
            return True, main_url
    except Exception as e:  # noqa: BLE001
        logger.debug(f"No server on main port {main_port}: {e}")

    return False, None


async def heartbeat_loop(docs_url: str) -> None:
    heartbeat_interval = 10

    while True:
        try:
            await post_json(f"{docs_url}/timeliner/heartbeat", {})
            logger.trace("Heartbeat sent")
        except Exception as e:  # noqa: BLE001
            logger.warning("Heartbeat failed: %s", e)

        await asyncio.sleep(heartbeat_interval)


class MkDocsBuilder:
    def __init__(self, work_folder: Path) -> None:
        self.work_folder = Path(work_folder).resolve()
        self.mkdocs_folder = CONFIG.config_folder
        self.hooks_folder = self.mkdocs_folder / "hooks"
        self.templates_folder = Path(__file__).parent / "mkdocs-template"
        self.regenerate_settings = CONFIG.mkdocs_regenerate_settings
        self.port: int | None = None
        self.process: asyncio.subprocess.Process | None = None
        self.serve_url: str | None = None
        self.log_handle: TextIO | None = None

    def _get_work_folder_short(self) -> str:
        """Get work folder path with up to 3 parent elements"""
        parts = self.work_folder.parts
        max_parts = 3
        if len(parts) <= max_parts:
            return str(self.work_folder)
        return str(Path(*parts[-max_parts:]))

    def _get_site_name(self) -> str:
        """Get site name from config or default"""
        if CONFIG.mkdocs_site_name:
            return CONFIG.mkdocs_site_name
        work_folder_short = self._get_work_folder_short()
        return f"Timeliner: {work_folder_short}"

    def _generate_config(self) -> str:
        template_path = self.templates_folder / CONFIG_FOLDER_NAME / "mkdocs.yml"
        template = template_path.read_text(encoding="utf-8")

        site_name = self._get_site_name()
        return template.replace("{{SITE_NAME}}", site_name).replace("{{CONFIG_FOLDER}}", CONFIG_FOLDER_NAME)

    def _generate_nav_config(self) -> str:
        template_path = self.templates_folder / ".nav.yml"
        template = template_path.read_text(encoding="utf-8")

        sort_direction = "desc" if CONFIG.mkdocs_reverse_navigation else "asc"
        return template.replace("{{SORT_DIRECTION}}", sort_direction)

    def _create_nav_file(self) -> None:
        """Create .nav.yml file in work folder"""
        nav_file = self.work_folder / ".nav.yml"
        if not self.regenerate_settings and nav_file.exists():
            logger.debug("Skipping .nav.yml regeneration (already exists)")
            return
        nav_config = self._generate_nav_config()
        nav_file.write_text(nav_config, encoding="utf-8")
        logger.debug(f"Created navigation config: {nav_file}")

    def _create_index_page(self) -> None:
        index_file = self.work_folder / "index.md"

        template_path = self.templates_folder / "index.md"
        template = template_path.read_text(encoding="utf-8")

        work_folder_full = str(self.work_folder.resolve())
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")

        content = (
            template.replace("{{TIMESTAMP}}", timestamp).replace("{{WORK_FOLDER_FULL}}", work_folder_full).replace("{{SERVE_URL}}", self.serve_url or "").replace("{{PORT}}", str(self.port or ""))
        )

        index_file.write_text(content, encoding="utf-8")
        logger.info(f"Regenerated welcome page: {index_file}")

    def _setup_hooks(self) -> None:
        self.hooks_folder.mkdir(parents=True, exist_ok=True)
        hooks_source_dir = self.templates_folder / CONFIG_FOLDER_NAME / "hooks"

        for hook_file in ["timeliner_server.py", "nav_titles.py", "unwatch_mkdocs.py", "gen_index.py"]:
            source_hook = hooks_source_dir / hook_file
            target_hook = self.hooks_folder / hook_file

            if not self.regenerate_settings and target_hook.exists():
                logger.debug(f"Skipping {hook_file} regeneration (already exists)")
                continue

            if source_hook.exists():
                shutil.copy2(source_hook, target_hook)
                logger.debug(f"Copied hook file to {target_hook}")
            else:
                logger.warning(f"Hook file not found at {source_hook}")

    def _setup_custom_css(self) -> None:
        css_filename = "timeliner-custom.css"
        overrides_dir = self.mkdocs_folder / "overrides"
        overrides_dir.mkdir(parents=True, exist_ok=True)

        source_css = self.templates_folder / CONFIG_FOLDER_NAME / "overrides" / css_filename
        target_css = overrides_dir / css_filename

        if not self.regenerate_settings and target_css.exists():
            logger.debug(f"Skipping {css_filename} regeneration (already exists)")
            return

        if source_css.exists():
            shutil.copy2(source_css, target_css)
            logger.debug(f"Copied custom CSS to {target_css}")
        else:
            logger.warning(f"Custom CSS file not found at {source_css}")

    def _try_bind_port(self, port: int, attempts: int = 1) -> bool:
        for attempt in range(attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", port))
                    return True
            except OSError:
                if attempt < attempts - 1:
                    logger.debug(f"Port {port} busy, retry {attempt + 1}/{attempts}...")
                    time.sleep(0.1)
        return False

    def _find_free_port(self) -> int | None:
        if CONFIG.mkdocs_port:
            port = CONFIG.mkdocs_port
            if self._try_bind_port(port, attempts=3):
                logger.info(f"Using CLI-specified port {port}")
                return port
            logger.error(f"CLI-specified port {port} busy after 3 attempts")
            return None

        folder_path = str(self.work_folder.resolve())
        hash_digest = hashlib.md5(folder_path.encode()).hexdigest()  # noqa: S324
        port_offset = int(hash_digest[:8], 16) % 1000
        base_port = 8000 + port_offset

        if self._try_bind_port(base_port, attempts=3):
            logger.info(f"Using stable port {base_port} (hash offset: {port_offset})")
            return base_port

        logger.info(f"Stable port {base_port} busy after 3 attempts, trying derivative ports...")

        for offset in range(1, 100):
            port = base_port + offset
            if self._try_bind_port(port):
                logger.info(f"Using derivative port {port} (base: {base_port})")
                return port

        logger.error(f"No free ports in range {base_port}-{base_port + 99}")
        return None

    async def _log_stream_reader(self, stream: asyncio.StreamReader, stream_name: str) -> None:
        """Read from stream and write timestamped lines to log file."""
        while True:
            try:
                line = await stream.readline()
                if not line:
                    break

                timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                decoded_line = line.decode("utf-8", errors="replace").rstrip("\n")
                log_entry = f"{timestamp} | {decoded_line}\n"

                if self.log_handle:
                    self.log_handle.write(log_entry)
                    self.log_handle.flush()
            except Exception as e:  # noqa: BLE001
                logger.error(f"Error reading {stream_name}: {e}")
                break

    async def _start_serve(self) -> tuple[bool, int | None]:
        try:
            config_file = self.mkdocs_folder / "mkdocs.yml"
            if not self.regenerate_settings and config_file.exists():
                logger.debug("Skipping mkdocs.yml regeneration (already exists)")
            else:
                config = self._generate_config()
                config_file.write_text(config, encoding="utf-8")

            port = self._find_free_port()
            if port is None:
                return False, None

            self.port = port

            logger.debug("Starting mkdocs serve on port %d", port)

            self.log_handle = open(MKDOCS_SERVER_LOG, "a")  # noqa: ASYNC230, SIM115, PTH123

            mkdocs_env = {
                **os.environ,
                "PYTHONUNBUFFERED": "1",
                "TIMELINER_WORK_FOLDER": str(self.work_folder.resolve()),
                "TIMELINER_SERVER": "localhost",
                "TIMELINER_PORT": str(port),
                "TIMELINER_MKDOCS_IDLE_TIMEOUT": str(CONFIG.mkdocs_idle_timeout),
            }

            self.process = await asyncio.create_subprocess_exec(
                "mkdocs",
                "serve",
                "--livereload",
                "-a",
                f"127.0.0.1:{port}",
                "-f",
                str(config_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.work_folder,
                env=mkdocs_env,
                start_new_session=True,
            )

            if self.process.stdout:
                asyncio.create_task(self._log_stream_reader(self.process.stdout, "stdout"))  # noqa: RUF006
            if self.process.stderr:
                asyncio.create_task(self._log_stream_reader(self.process.stderr, "stderr"))  # noqa: RUF006

            await asyncio.sleep(1.0)

            if self.process.returncode is not None:
                logger.error(f"mkdocs serve exited immediately with code {self.process.returncode}")
                return False, None

            return True, port  # noqa: TRY300

        except FileNotFoundError:
            logger.error("mkdocs command not found - please install mkdocs")
            return False, None
        except Exception as e:  # noqa: BLE001
            error_msg = f"Failed to start mkdocs serve: {e}"
            logger.error(error_msg)
            return False, None

    def _create_gitignore(self) -> None:
        mkdocs_template = self.templates_folder / CONFIG_FOLDER_NAME / "gitignore"
        mkdocs_gitignore = self.mkdocs_folder / ".gitignore"
        if not self.regenerate_settings and mkdocs_gitignore.exists():
            logger.debug("Skipping .tliner/.gitignore regeneration (already exists)")
        else:
            mkdocs_content = mkdocs_template.read_text(encoding="utf-8")
            mkdocs_gitignore.write_text(mkdocs_content, encoding="utf-8")
            logger.debug(f"Created .gitignore in {self.mkdocs_folder}")

        workfolder_template = self.templates_folder / "gitignore"
        workfolder_gitignore = self.work_folder / ".gitignore"
        if not self.regenerate_settings and workfolder_gitignore.exists():
            logger.debug("Skipping work folder .gitignore regeneration (already exists)")
        else:
            workfolder_content = workfolder_template.read_text(encoding="utf-8")
            workfolder_gitignore.write_text(workfolder_content, encoding="utf-8")
            logger.debug(f"Created .gitignore in {self.work_folder}")

    async def initial_serve(self) -> bool:
        logger.info("Starting MkDocs documentation server...")

        self.mkdocs_folder.mkdir(parents=True, exist_ok=True)
        clear_logs_folder()
        self._create_gitignore()
        self._setup_hooks()
        self._setup_custom_css()
        self._create_nav_file()

        success, port = await self._start_serve()

        if success and port:
            self.serve_url = f"http://localhost:{port}"
            self.port = port

            logger.info(f"📚 Docs available at: {self.serve_url}")

            if CONFIG.mkdocs_auto_open:
                try:
                    webbrowser.open(self.serve_url)
                    logger.info("Opened documentation in browser")
                except Exception as e:  # noqa: BLE001
                    logger.warning("Could not auto-open browser: %s", e)

            return True

        logger.error("Failed to start MkDocs server")
        return False

    async def stop(self) -> None:
        if self.process and self.process.returncode is None:
            logger.info("Stopping MkDocs server...")

            self.process.terminate()

            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
                logger.debug("MkDocs server stopped gracefully")
            except TimeoutError:
                logger.warning("MkDocs server did not stop gracefully, forcing kill")
                self.process.kill()
                await self.process.wait()

            logger.info("MkDocs server stopped")

        if self.log_handle:
            self.log_handle.close()
            self.log_handle = None


_builder_instance: MkDocsBuilder | None = None
_heartbeat_task: asyncio.Task | None = None


async def initialize_mkdocs() -> MkDocsBuilder | None:
    global _builder_instance, _heartbeat_task  # noqa: PLW0603

    if not CONFIG.mkdocs:
        logger.debug("MkDocs integration disabled (--no-mkdocs)")
        return None

    logger.info("Initializing MkDocs integration...")

    # Check for existing server
    is_running, docs_url = await check_existing_server()
    if is_running and docs_url:
        logger.info(f"Reusing existing MkDocs server: {docs_url}")

        _heartbeat_task = asyncio.create_task(heartbeat_loop(docs_url))

        if CONFIG.mkdocs_auto_open:
            try:
                webbrowser.open(docs_url)
                logger.info("Opened documentation in browser")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Could not auto-open browser: {e}")

        return None

    # no existing server found, start a new one
    builder = MkDocsBuilder(CONFIG.work_folder)
    success = await builder.initial_serve()

    if success and builder.serve_url:
        _builder_instance = builder

        docs_url_file = CONFIG.work_folder / "docs.url"
        docs_url_file.write_text(builder.serve_url)
        desktop_file = CONFIG.work_folder / "docs.desktop"
        desktop_file.write_text(f"[Desktop Entry]\nType=Link\nURL={builder.serve_url}\nIcon=text-html\n")
        desktop_file.chmod(0o755)
        logger.info(f"Wrote docs.url: {builder.serve_url}")

        _heartbeat_task = asyncio.create_task(heartbeat_loop(builder.serve_url))

        return builder

    logger.warning("MkDocs initialization failed - continuing without documentation")
    return None


def shutdown_mkdocs() -> None:
    global _builder_instance, _heartbeat_task  # noqa: PLW0603

    if _heartbeat_task:
        _heartbeat_task.cancel()
        logger.info("Stopped MkDocs heartbeat (server will idle out naturally)")
        _heartbeat_task = None

    if _builder_instance:
        try:
            if _builder_instance.log_handle:
                _builder_instance.log_handle.close()
                logger.debug("Closed MkDocs log handle")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error during MkDocs shutdown: {e}")
        finally:
            _builder_instance = None
