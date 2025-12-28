import logging
from pathlib import Path
from typing import Any

log = logging.getLogger("mkdocs")


def on_serve(server: Any, config: Any, **kwargs: Any) -> Any:
    mkdocs_dir = Path(config.docs_dir) / ".tliner"
    mkdocs_dir_str = str(mkdocs_dir.resolve())

    log.info(f"[UNWATCH HOOK] Setting up filter for: {mkdocs_dir_str}")

    docs_dir_abs = str(Path(config.docs_dir).resolve())

    if docs_dir_abs in server._watch_refs:  # noqa: SLF001
        watch_ref = server._watch_refs[docs_dir_abs]  # noqa: SLF001

        for emitter in server.observer.emitters:
            if hasattr(emitter, "_watch") and emitter._watch == watch_ref:  # noqa: SLF001
                original_queue_event = emitter.queue_event

                def filtered_queue_event(event: Any, _orig=original_queue_event) -> Any:
                    if mkdocs_dir_str not in event.src_path:
                        return _orig(event)
                    log.debug("[UNWATCH HOOK] Filtered: %s", event.src_path)
                    return None

                emitter.queue_event = filtered_queue_event
                log.info(f"[UNWATCH HOOK] Patched emitter for {docs_dir_abs}")
                break

    return server
