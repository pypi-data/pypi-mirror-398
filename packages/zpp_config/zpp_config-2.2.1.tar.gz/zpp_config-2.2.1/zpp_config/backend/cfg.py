import configparser
from .global_backend import ConfigBackend

class CfgBackend(ConfigBackend):
    """Backend pour les fichiers .cfg (par exemple, des fichiers de configuration de type clé-valeur)."""

    def load(self, filename):
        """Charge le fichier .cfg en dictionnaire depuis un Path ou fichier ouvert."""
        # Utilisation de ConfigParser qui peut également lire des fichiers de type clé-valeur simples
        parser = configparser.ConfigParser()
        parser.optionxform = str  # Garder la casse des clés
        parser.read(filename, encoding='utf-8')

        data = {}
        for section in parser.sections():
            data[section] = dict(parser.items(section))  # Enregistrer chaque section comme un dictionnaire
        return data

    def load_data(self, rendered):
        """Charge un contenu .cfg sous forme de chaîne en dictionnaire."""
        parser = configparser.ConfigParser(allow_no_value=True)
        parser.optionxform = str
        
         # Ajouter une section par défaut, pour éviter l'erreur
        rendered_with_section = "[default]\n" + rendered  # Ajouter une section par défaut
        parser.read_string(rendered_with_section)

        data = {}
        for section in parser.sections():
            data[section] = dict(parser.items(section))
        return data

    def save(self, filename, data):
        """Écrit un dictionnaire en fichier .cfg."""
        parser = configparser.ConfigParser()
        parser.optionxform = str
        for section, values in data.items():
            parser[section] = values  # Chaque section est un dictionnaire clé-valeur
        with open(filename, 'w', encoding='utf-8') as f:
            parser.write(f)
