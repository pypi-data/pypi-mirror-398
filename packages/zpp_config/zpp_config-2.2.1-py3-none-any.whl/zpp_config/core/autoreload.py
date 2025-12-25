from pathlib import Path
from watchdog.events import FileSystemEventHandler


class _ConfigFileEventHandler(FileSystemEventHandler):
    def __init__(self, config):
        self._config = config
        self._config_path = self._config._filename.resolve()  # chemin absolu

    def on_modified(self, event):
        try:
            event_path = Path(event.src_path).resolve()
            if event_path == self._config_path:
                self._config.reload()
                if self._config._on_reload:
                    self._config._on_reload(self._config)
        except Exception as e:
            print(f"[Config autoreload] erreur lors du reload: {e}")