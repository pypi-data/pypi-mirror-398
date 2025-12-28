import json
from .global_backend import ConfigBackend

class JsonBackend(ConfigBackend):
    """Backend pour les fichiers JSON."""
    def load(self, filename):
        return json.loads(filename.read_text())

    def load_data(self, rendered):
        return json.loads(rendered) if rendered.strip() else {}

    def save(self, filename, data):
        filename.write_text(json.dumps(data, indent=4))