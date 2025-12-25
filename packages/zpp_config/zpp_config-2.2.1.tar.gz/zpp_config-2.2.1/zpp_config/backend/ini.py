import configparser
from .global_backend import ConfigBackend

class IniBackend(ConfigBackend):
    """Backend pour les fichiers INI."""

    def load(self, filename):
        """Charge le fichier INI en dictionnaire depuis un Path ou fichier ouvert."""
        parser = configparser.ConfigParser()
        parser.optionxform = str  # garder la casse des clés
        parser.read(filename, encoding='utf-8')

        data = {}
        for section in parser.sections():
            data[section] = dict(parser.items(section))
        return data

    def load_data(self, rendered):
        """Charge un contenu INI sous forme de chaîne en dictionnaire."""
        parser = configparser.ConfigParser()
        parser.optionxform = str
        parser.read_string(rendered)

        data = {}
        for section in parser.sections():
            data[section] = dict(parser.items(section))
        return data

    def save(self, filename, data):
        """Écrit un dictionnaire en fichier INI."""
        parser = configparser.ConfigParser()
        parser.optionxform = str
        for section, values in data.items():
            parser[section] = values
        with open(filename, 'w', encoding='utf-8') as f:
            parser.write(f)
