import yaml
from .global_backend import ConfigBackend

class YamlBackend(ConfigBackend):
    """Backend pour les fichiers YAML."""
    def load(self, filename):
        return yaml.safe_load(filename.read_text()) or {}

    def load_data(self, rendered):
        return yaml.safe_load(rendered) or {}

    def save(self, filename, data):
        filename.write_text(yaml.safe_dump(data, sort_keys=True))