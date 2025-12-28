import impmagic
from jinja2 import FileSystemLoader
from pathlib import Path

class ValidationError(Exception):
    pass


class SafeFileSystemLoader(FileSystemLoader):
    def get_source(self, environment, template):
        try:
            return super().get_source(environment, template)

        except UnicodeDecodeError:
            # Reconstruction du chemin réel
            for searchpath in self.searchpath:
                filename = Path(searchpath) / template
                if filename.exists():
                    break
            else:
                raise

            # Fallback Windows
            with open(filename, "r", encoding="cp1252") as f:
                source = f.read()

            return source, str(filename), lambda: False


## Méthode Jinja2
@impmagic.loader(
    {'module':'os'},
)
def env(var_name, default=None):
    return os.environ.get(var_name, default)

@impmagic.loader(
    {'module':'zpp_config.core.vault', 'submodule': ['Vault']},
)
def get_vault_key(vault_file, key, vault_password=None, vault_keyfile=None):
    v = Vault(vault_file, password=vault_password, keyfile=vault_keyfile)
    return v.get_key(key)
## Méthode Jinja2

class ConfigNode:
    """Gère uniquement la hiérarchie et l'accès aux données"""

    def __init__(self, config=None, path="", _data=None):
        self._config = config
        self._path = path
        self._data = _data

    def _root_data(self):
        """Retourne la référence au dictionnaire de données racine."""
        return self._config._data if self._config else self._data

    def _full_path(self, path):
        """Construit le chemin complet (ex: 'parent.enfant')."""
        return f"{self._path}.{path}" if self._path else path


    def _get_value(self):
        """Récupère le dictionnaire ou la valeur associé à ce noeud."""
        node = self._root_data()
        if not self._path:
            return node
        for k in self._path.split("."):
            if k not in node or not isinstance(node[k], dict):
                #node[k] = {}
                return None
            node = node[k]
        return node

    def __getattr__(self, key):
        if key.startswith("_"):
            raise AttributeError

        # autoload uniquement si on est la racine
        root_node = self._config if self._config else self
        if root_node and isinstance(root_node, Config):
            object.__getattribute__(root_node, "_autoload")()

        val = self._get_value()
        if not isinstance(val, dict) or key not in val:
            return None

        return ConfigNode(self._config or self, self._full_path(key)) if isinstance(val[key], dict) else val[key]


    def __setattr__(self, key, value):
        if key.startswith("_"):
            return super().__setattr__(key, value)

        # autoload
        object.__getattribute__(self, "_autoload")()

        self.set(key, value)


    def __delattr__(self, key):
        self.delete(key)

    def _get_root_data(self):
        # Root data = _config._data si on est dans un ConfigNode enfant, sinon _data
        return self._config._data if self._config else self._data

    def items(self):
        # autoload
        object.__getattribute__(self, "_autoload")()

        val = self._get_value()
        if isinstance(val, dict):
            for k, v in val.items():
                yield k, ConfigNode(self._config or self, f"{self._full_path(k)}")

    def keys(self):
        # autoload
        object.__getattribute__(self, "_autoload")()

        val = self._get_value()
        return val.keys() if isinstance(val, dict) else []

    def values(self):
        # autoload
        object.__getattribute__(self, "_autoload")()

        val = self._get_value()
        if isinstance(val, dict):
            for k in val:
                yield ConfigNode(self._config or self, f"{self._full_path(k)}")

    def get(self, path, default=None, strict: bool = False):
        # autoload
        object.__getattribute__(self, "_autoload")()

        keys = self._full_path(path).split(".")
        node = self._root_data()
        for k in keys:
            if not isinstance(node, dict) or k not in node:
                if strict:
                    raise KeyError(path)
                return default
            node = node[k]
        return node

    def set(self, path, value):
        # autoload
        object.__getattribute__(self, "_autoload")()

        keys = self._full_path(path).split(".")
        node = self._root_data()
        for k in keys[:-1]:
            if k not in node or not isinstance(node[k], dict):
                node[k] = {}
            node = node[k]
        node[keys[-1]] = value

        # Auto-save
        root_node = self._config if self._config else self
        if hasattr(root_node, '_auto_save') and root_node._auto_save:
            root_node.save()

    def delete(self, path):
        # autoload
        object.__getattribute__(self, "_autoload")()

        keys = self._full_path(path).split(".")
        node = self._root_data()
        for k in keys[:-1]:
            if k not in node or not isinstance(node[k], dict):
                return
            node = node[k]
        node.pop(keys[-1], None)
        
        # Auto-save
        root_node = self._config if self._config else self
        if hasattr(root_node, '_auto_save') and root_node._auto_save:
            root_node.save()

    def merge(self, data, overload=False):
        """Fusionne un dict complet dans la racine."""
        # autoload
        object.__getattribute__(self, "_autoload")()

        # locate the node data
        node = self._get_value()
        if not isinstance(node, dict):
            raise TypeError(f"Cannot merge into a non-dict node at {self._path}")

        # perform merge
        root = self._config or self
        root._deep_merge(node, data, overload)

        if root._auto_save:
            root.save()


    def update(self, path, data, overload=False):
        """Met à jour une partie de la config sans écraser le reste."""
        # autoload
        object.__getattribute__(self, "_autoload")()

        root = self._config or self

        node = self.get(path)  # ou équivalent
        if not isinstance(node, dict):
            raise TypeError(f"Cannot update non-dict node at {path}")
        root._deep_merge(node, data, overload)

        if root._auto_save:
            root.save()


    def __getitem__(self, path):
        """Permet l'accès par index (config['chemin.vers.clef'])."""
        # autoload
        object.__getattribute__(self, "_autoload")()

        value = self.get(path)
        
        # Si la valeur est un dict, on retourne un ConfigNode pour continuer l'accès.
        if isinstance(value, dict):
             return ConfigNode(self._config or self, self._full_path(path))
        
        # Si la valeur est None (valeur par défaut de get() quand non trouvée), 
        # on lève une KeyError pour se comporter comme un dictionnaire standard.
        if value is None:
            raise KeyError(path)
            
        return value

    def __setitem__(self, path, value):
        """Permet la modification par index (config['chemin.vers.clef'] = valeur)."""
        # autoload
        object.__getattribute__(self, "_autoload")()

        self.set(path, value)

    def to_dict(self) -> dict:
        """Retourne la configuration complète (ou du noeud actuel) comme un dictionnaire Python standard."""
        # autoload
        object.__getattribute__(self, "_autoload")()

        return self._get_value()

    def __iter__(self):
        # autoload
        object.__getattribute__(self, "_autoload")()

        return iter(self.keys())

    def __repr__(self):
        # autoload
        object.__getattribute__(self, "_autoload")()

        return repr(self._get_value())

    def __str__(self):
        # autoload
        object.__getattribute__(self, "_autoload")()

        return str(self._get_value())

    @impmagic.loader(
        {'module':'json'},
    )
    def to_json(self, indent: int = 4) -> str:
        """Retourne la configuration en JSON formaté."""
        # autoload
        object.__getattribute__(self, "_autoload")()

        return json.dumps(self.to_dict(), indent=indent)

    @impmagic.loader(
        {'module':'yaml'},
    )
    def to_yaml(self, sort_keys: bool = True) -> str:
        """Retourne la configuration en YAML formaté."""
        # autoload
        object.__getattribute__(self, "_autoload")()

        return yaml.safe_dump(self.to_dict(), sort_keys=sort_keys)

    @impmagic.loader(
        {'module':'toml'},
    )
    def to_toml(self) -> str:
        """Retourne la configuration en TOML formaté."""
        # autoload
        object.__getattribute__(self, "_autoload")()

        return toml.dumps(self.to_dict())

    def _autoload(self):
        # autoload uniquement si on est la racine
        root_node = self._config if self._config else self
        if isinstance(root_node, Config):
            object.__getattribute__(root_node, "ensure_loaded")()

    def __contains__(self, key) -> bool:
        # autoload
        object.__getattribute__(self, "_autoload")()

        # Cas chemin pointé (ex: "db.host")
        if "." in key:
            parts = key.split(".")
            node = self  # commence par ce nœud
            for part in parts:
                val = object.__getattribute__(node, "_get_value")()
                if not isinstance(val, dict) or part not in val:
                    return False
                # créer un ConfigNode pour le prochain niveau
                node = ConfigNode(node._config or node, node._full_path(part))
            return True

        # Cas clé simple
        val = object.__getattribute__(self, "_get_value")()
        if not isinstance(val, dict):
            return False
        return key in val

    def __eq__(self, other):
        """Compare le contenu du nœud avec un autre ConfigNode ou dict."""
        # autoload
        object.__getattribute__(self, "_autoload")()

        if isinstance(other, ConfigNode):
            return self.to_dict() == other.to_dict()
        return self.to_dict() == other

    def __ne__(self, other):
        """Inverse de __eq__."""
        # autoload
        object.__getattribute__(self, "_autoload")()

        return not self.__eq__(other)

    def __bool__(self):
        """Retourne True si le nœud contient une valeur ou des sous-clés."""
        # autoload
        object.__getattribute__(self, "_autoload")()

        val = self._get_value()
        return bool(val)

    def __delitem__(self, path):
        """Permet de supprimer une clé par index (config['chemin.vers.clef'])."""
        # autoload
        object.__getattribute__(self, "_autoload")()
        
        self.delete(path)


class Config(ConfigNode):
    @impmagic.loader(
        {'module':'os'},
        {'module':'zpp_config.backend.yaml', 'submodule': ['YamlBackend']},
        {'module':'zpp_config.backend.json', 'submodule': ['JsonBackend']},
        {'module':'zpp_config.backend.toml', 'submodule': ['TomlBackend']},
        {'module':'zpp_config.backend.ini', 'submodule': ['IniBackend']},
        {'module':'zpp_config.backend.cfg', 'submodule': ['CfgBackend']},
        {'module':'pathlib', 'submodule': ['Path']},
        {'module':'jinja2', 'submodule': ['Environment']},
        {'module':'zpp_config.core.vault_encryption', 'submodule': ['vault_decrypt']},
    )
    def __init__(self, filename, filetype=None, context=None, vault_file=None, vault_keyfile=None, vault_password=None, vault_encryption_keyfile=None, vault_encryption_password=None):
        self._filename = Path(filename)
        self._context = context or {}

        self._vault_file = vault_file
        self._vault_keyfile = vault_keyfile
        self._vault_password = vault_password

        self._vault_encryption_keyfile = vault_encryption_keyfile
        self._vault_encryption_password = vault_encryption_password

        self._autoreload_enabled = False
        self._observer = None
        self._on_reload = None

        # Environment Jinja2 personnalisable
        self._env = Environment(
            loader=SafeFileSystemLoader(self._filename.parent),
            autoescape=False
        )

        # Fonction pour récupérer une clé dans un vault
        def vault(key):
            return get_vault_key(self._vault_file, key, vault_password=self._vault_password, vault_keyfile=self._vault_keyfile)

        # Fonction pour déchiffrer une clé avec vault_encryption
        def vault_encryption(key):
            password = self._vault_encryption_password

            if self._vault_encryption_keyfile and os.path.exists(self._vault_encryption_keyfile):
                with open(self._vault_encryption_keyfile, "r") as f:
                    password = f.read().strip('\n')

            return vault_decrypt(key, password)


        # Ajout de la méthode env() dans jinja
        self._env.globals["env"] = env
        self._env.globals["vault"] = vault
        self._env.globals["vault_encryption"] = vault_encryption

        # Détection automatique du filetype pour le backend
        if filetype is None:
            ext = self._filename.suffix.lower()
            if ext in (".yaml", ".yml"):
                filetype = "yaml"
            elif ext == ".json":
                filetype = "json"
            elif ext == ".toml":
                filetype = "toml"
            elif ext == ".ini":
                filetype = "ini"
            elif ext == ".cfg":
                filetype = "cfg"
            else:
                raise ValueError(f"Impossible de détecter le type de fichier depuis l'extension {ext}")

        # Sélection du backend
        filetype = filetype.lower()
        if filetype == "yaml":
            backend = YamlBackend()
        elif filetype == "json":
            backend = JsonBackend()
        elif filetype == "toml":
            backend = TomlBackend()
        elif filetype == "ini":
            backend = IniBackend()
        elif filetype == "cfg":
            backend = CfgBackend()
        else:
            raise ValueError(f"Type de fichier non supporté: {filetype}. Types supportés: yaml, json, toml, ini, cfg.")

        self._backend = backend
        self._auto_save = False
        self._loaded = False
        super().__init__(path="", _data={})

    def load(self):
        """Render Jinja + parse via backend"""
        if not self._filename.exists():
            self._data = {}
            self._loaded = True

        else:
            template = self._env.get_template(self._filename.name)
            data_render = template.render(**self._context)

            self._data = self._backend.load_data(data_render)
            self._loaded = True

    def reload(self):
        """Re-render si le context a changé"""
        return self.load()

    @impmagic.loader(
        {'module':'pathlib', 'submodule': ['Path']},
    )
    def save(self, filepath=None):
        if filepath:
            filepath = Path(filepath)
        else:
            filepath = self._filename

        filepath.parent.mkdir(parents=True, exist_ok=True)
        self._backend.save(filepath, self._data)

    def auto_save(self, enabled: bool):
        self._auto_save = enabled

    @impmagic.loader(
        {'module':'yaml'},
        {'module':'json'},
        {'module':'toml'},
        {'module':'pathlib', 'submodule': ['Path']},
    )
    def export(self, filepath, type = "yaml", sort_keys: bool = True):
        """
        Exporte la configuration (ou un sous-noeud) en YAML / JSON / TOML.
        Retourne une chaîne (n'écrit pas dans un fichier).
        """
        filepath = Path(filepath)

        type = type.lower()
        data = self.to_dict()

        if type == "yaml":
            content = yaml.safe_dump(data, sort_keys=sort_keys)

        elif type == "json":
            content = json.dumps(data, indent=4, sort_keys=sort_keys)

        elif type == "toml":
            content = toml.dumps(data)

        else:
            raise ValueError(
                f"Format '{type}' non supporté. Formats autorisés: yaml, json, toml."
            )

        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content)

    # Jinja helpers
    def register_filter(self, name, func):
        """Register a filter in the Jinja environment."""
        self._env.filters[name] = func

    def register_test(self, name, func):
        """Register a test in the Jinja environment."""
        self._env.tests[name] = func

    def register_global(self, name, obj):
        """Register a global in the Jinja environment."""
        self._env.globals[name] = obj

    def ensure_loaded(self):
        loaded = object.__getattribute__(self, "_loaded")
        if not loaded:
            self.load()

    def set_context(self, context):
        self._context = context

    def _deep_merge(self, config_dict, data_dict, overload):
        for key, value in data_dict.items():
            if key in config_dict:
                if isinstance(config_dict[key], dict) and isinstance(value, dict):
                    self._deep_merge(config_dict[key], value, overload)
                else:
                    if overload:
                        config_dict[key] = value
            else:
                config_dict[key] = value

    ## Partie validate
    def validate(self, schema=None, rules=None, strict=True):
        """Valide la configuration selon un schéma et/ou des règles globales."""
        self.ensure_loaded()

        errors = []

        if schema is not None:
            errors += self._validate_schema(self.to_dict(), schema, prefix="")

        if rules is not None:
            errors += self._validate_rules(self.to_dict(), rules)

        if errors and strict:
            raise ValidationError("\n".join(errors))

        return errors

    def _validate_schema(self, data, schema, prefix=""):
        """Validation hiérarchique selon un schéma dict."""
        errors = []

        for key, rule in schema.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(rule, dict) and any(k.startswith("_") for k in rule.keys()):
                # Validations sur une feuille
                value = data.get(key)
                errors += self._check_value(full_key, value, rule)

            else:
                # Descente récursive
                value = data.get(key)
                if value is None:
                    continue
                if not isinstance(value, dict):
                    errors.append(f"{full_key}: expected dict, got {type(value).__name__}")
                else:
                    errors += self._validate_schema(value, rule, prefix=full_key)

        return errors

    @impmagic.loader(
        {'module':'re'},
    )
    def _validate_rules(self, data, rules, match_on="name"):
        """
        Valide la config selon les rules. Les keys des rules sont des regex sur le nom des clés finales.
        match_on: "name" -> regex sur le dernier segment (default)
                  "path" -> regex sur le chemin complet
        """
        errors = []

        def _recurse(node, path=""):
            if not isinstance(node, dict):
                return

            for key, value in node.items():
                full_path = f"{path}.{key}" if path else key

                # Détermine la cible à tester pour la regex
                target = key if match_on == "name" else full_path

                for pattern, rule in rules.items():
                    if re.search(pattern, target):
                        errors.extend(self._check_value(full_path, value, rule))

                # Récursion
                if isinstance(value, dict):
                    _recurse(value, full_path)

        _recurse(data)
        return errors

    def _flatten_dict(self, d, parent=""):
        """Transforme un dict en { 'db.host': 'localhost', ... }"""
        items = {}
        for k, v in d.items():
            new_key = f"{parent}.{k}" if parent else k
            if isinstance(v, dict):
                items.update(self._flatten_dict(v, new_key))
            else:
                items[new_key] = v
        return items

    @impmagic.loader(
        {'module':'re'},
    )
    def _check_value(self, path, value, rule):
        errors = []
        desc = rule.get("_desc", path)

        # _required
        if rule.get("_required") and value is None:
            errors.append(f"{desc}: required value missing")
            return errors

        if value is None:
            return errors  # nothing else to validate

        # _type
        if "_type" in rule:
            expected = rule["_type"]
            if not isinstance(value, expected):
                errors.append(f"{desc}: expected type {expected.__name__}, got {type(value).__name__}")

        # Numeric checks
        if isinstance(value, (int, float)):
            if "_min" in rule and value < rule["_min"]:
                errors.append(f"{desc}: {value} < min {rule['_min']}")
            if "_max" in rule and value > rule["_max"]:
                errors.append(f"{desc}: {value} > max {rule['_max']}")

        # String checks
        if isinstance(value, str):
            if "_len" in rule and len(value) != rule["_len"]:
                errors.append(f"{desc}: length {len(value)} != {rule['_len']}")
            if "_min_len" in rule and len(value) < rule["_min_len"]:
                print("okpodkqz")
                errors.append(f"{desc}: length {len(value)} < min_len {rule['_min_len']}")
            if "_max_len" in rule and len(value) > rule["_max_len"]:
                errors.append(f"{desc}: length {len(value)} > max_len {rule['_max_len']}")
            if "_regex" in rule:
                if not re.fullmatch(rule["_regex"], value):
                    errors.append(f"{desc}: '{value}' does not match regex {rule['_regex']}")

        # Enum
        if "_enum" in rule and value not in rule["_enum"]:
            errors.append(f"{desc}: '{value}' not in allowed values {rule['_enum']}")

        # Not value
        if "_not" in rule and value == rule["_not"]:
            errors.append(f"{desc}: value not allowed: {value}")

        return errors
    ## Partie validate

    ## Partie autoreload
    @impmagic.loader(
        {'module':'watchdog.observers', 'submodule': ['Observer']},
        {'module':'zpp_config.core.autoreload', 'submodule': ['_ConfigFileEventHandler']},
    )
    def autoreload(self, enable: bool = True):
        """Active ou désactive l'autoreload via watchdog."""
        if enable and not self._autoreload_enabled:
            event_handler = _ConfigFileEventHandler(self)
            observer = Observer()
            observer.schedule(event_handler, str(self._filename.parent), recursive=False)
            observer.daemon = True  # ne bloque pas la fermeture du programme
            observer.start()
            self._observer = observer
            self._autoreload_enabled = True
        elif not enable and self._autoreload_enabled:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            self._autoreload_enabled = False

    def stop_autoreload(self):
        """Arrête le thread watchdog proprement."""
        self.autoreload(enable=False)
    ## Partie autoreload