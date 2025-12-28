from tomlkit import parse, dumps
from tomlkit.items import Table, Array
from tomlkit.toml_document import TOMLDocument
from .global_backend import ConfigBackend

#Convertisseur pour transformer les objets TOML en dictionnaire
def tomlkit_to_dict(obj):
    if isinstance(obj, (TOMLDocument, Table)):
        return {k: tomlkit_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, Array):
        return [tomlkit_to_dict(v) for v in obj]
    else:
        return obj

class TomlBackend(ConfigBackend):
    """NOUVEAU: Backend pour les fichiers TOML."""
    def load(self, filename):
        doc = parse(filename.read_text())
        return tomlkit_to_dict(doc)

    def load_data(self, rendered):
        if not rendered.strip():
            return {}
        doc = parse(rendered)
        return tomlkit_to_dict(doc)

    def save(self, filename, data):
        filename.write_text(dumps(data))
