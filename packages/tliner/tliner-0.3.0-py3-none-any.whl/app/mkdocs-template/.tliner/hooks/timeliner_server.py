import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("mkdocs.hooks.timeliner")


class IdleTimeoutMonitor:
    def __init__(self, server: Any, timeout: int = 300) -> None:
        self.server = server
        self.timeout = timeout
        self.last_request_time = time.time()
        self.last_activity_monotonic = time.monotonic()
        self.shutdown_initiated = False
        self.monitor_thread: threading.Thread | None = None
        self.work_folder: Path | None = None
        self.mkdocs_port: int | None = None

    def update_activity(self) -> None:
        self.last_request_time = time.time()
        self.last_activity_monotonic = time.monotonic()

    def start(self) -> None:
        def monitor_loop() -> None:
            while not self.shutdown_initiated:
                time.sleep(30)
                idle_time = time.monotonic() - self.last_activity_monotonic

                if idle_time > self.timeout:
                    log.info("[Timeliner] Idle for %ds, shutting down...", int(idle_time))
                    self.shutdown_initiated = True
                    if self.server:
                        try:
                            self.server.shutdown()
                        except Exception:
                            log.exception("[Timeliner] Shutdown error")
                    break

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        log.info("[Timeliner] Idle timeout monitor started (%ds)", self.timeout)


_monitor: IdleTimeoutMonitor | None = None


def on_serve(server: Any, config: dict[str, Any], builder: Any, **kwargs: Any) -> Any:
    global _monitor  # noqa: PLW0603

    work_folder = Path(os.getenv("TIMELINER_WORK_FOLDER", ".")).resolve()
    mkdocs_port = int(os.getenv("TIMELINER_PORT", "8000"))
    idle_timeout = int(os.getenv("TIMELINER_MKDOCS_IDLE_TIMEOUT", "300"))

    _monitor = IdleTimeoutMonitor(server, idle_timeout)
    _monitor.work_folder = work_folder
    _monitor.mkdocs_port = mkdocs_port

    log.info("[Timeliner] Initialized for %s", work_folder)

    original_serve_request = server._serve_request  # noqa: SLF001

    def custom_serve_request(self: Any, environ: dict[str, Any], start_response: Any) -> list[bytes]:
        if _monitor:
            _monitor.update_activity()

        path = environ["PATH_INFO"]
        log.debug("[Timeliner] Request: %s", path)

        if path == "/timeliner/metadata":
            data = {"work_folder": str(_monitor.work_folder), "mkdocs_port": _monitor.mkdocs_port, "status": "running"}
            log.info("[Timeliner] Serving metadata endpoint")
            start_response("200 OK", [("Content-Type", "application/json")])
            return [json.dumps(data).encode()]

        if path == "/timeliner/heartbeat" and _monitor:
            _monitor.update_activity()
            log.info("[Timeliner] Heartbeat received")
            start_response("200 OK", [("Content-Type", "application/json")])
            return [b'{"status": "alive"}']

        return original_serve_request(environ, start_response)

    import types  # noqa: PLC0415

    server._serve_request = types.MethodType(custom_serve_request, server)  # noqa: SLF001

    if _monitor:
        _monitor.start()

    return server
