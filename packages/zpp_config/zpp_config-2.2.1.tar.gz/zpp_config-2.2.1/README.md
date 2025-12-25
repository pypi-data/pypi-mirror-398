# Présentation

Ce module fournit un système complet de **gestion de fichiers de configuration** permettant :

- YAML / JSON / TOML  
- Templates Jinja2 (avec variables, `env()`, `vault()`, `vault_encryption()`)  
- Chargement lazy - Auto-save - Export  
- Validation via schéma hiérarchique et règles globales  
- Accès dynamique par attributs _ou_ indexés (`cfg.db.host`)  
- Merge / Update sans écrasement  
- Auto-reload du fichier via **watchdog**  
- Compatibilité Vault (clé protégée et décryptage)

# Installation

```console
[user@host ~]# pip install zpp_config
```

# Utilisation

### Initialisation

```python
from zpp_config import Config

config = Config("config.yaml")
```

Le backend est automatiquement choisi selon l’extension du fichier, mais il est possible de définir le type de configuration avec l'attribut **filetype** (yaml, json ou toml).

Lors de l'initialisation, il est également possible de définir plusieurs paramètres qui seront utile pour le render Jinja.

**context**:  défini un dictionnaire contenant les variables Jinja
**vault_file**: emplacement du fichier vault
**vault_keyfile**: emplacement du fichier contenant le mot de passe du vault
**vault_password**: mot de passe du vault
**vault_encryption_keyfile**: emplacement du fichier contenant le mot de passe du vault_encryption
**vault_encryption_password**: mot de passe du vault_encryption

```python
from core.config import Config

config = Config(
    "config.yaml",
    context={"env": "prod"},
    vault_file="secrets.vlt",
    vault_encryption_password="1234"
)
```

#### set_context()

Il est possible de redéfinir le context après chargement grâce à:

```python
config.set_context({"env": "staging", "debug": True})
config.reload()   # re-rend le template avec le nouveau contexte
```

### Chargement du fichier

Il est possible de forcer le chargement du fichier avec la méthode **load**

```python
config.load()
```

Toutefois, la configuration sera chargé automatiquement lors du premier appel de la configuration.

#### Auto-reload

Il est possible d'activer l'auto-reload pour permet de recharger la configuration dans le cas où le fichier de configuration change

```python
config.autoreload(True)
```

Il est possible de définir un callback a déclenché lorsque la configuration est rechargé

```python
def on_reload(cfg):
    print("Configuration rechargée !")

config._on_reload = on_reload
config.autoreload(True)
```

On est également désactiver l'auto-reload avec:
```python
config.stop_autoreload()
```

### Accès aux valeurs

#### Par attributs
```python
db_host = config.db.host
```
#### Par index
```python
db_host = config["db.host"]
```
#### Par get()
```python
db_host = config.get("db.host", default="127.0.0.1")
```
#### Itération
```python
for key, sub in config.db.items():
   print(key, sub.to_dict())
```

#### Vérifier l’existence d’un chemin
```python
"db.host" in config   # True / False
```

### Modification des valeurs

```python
config.db.user = "admin"
config["db.password"] = "secret"
config.set("feature.enable", True)
config.delete("db.password")
```

Toutes les modifications sont gardées en mémoire tant qu’on ne sauvegarde pas.

### Suppression des valeurs

```python
config.delete("db.password")
del config["db.password"]
del config.db.password
```

### Sauvegarde

#### Sauvegarde manuelle

Pour sauvegarder la configuration, on utilise la méthode **save**

```python
config.save()
```

L'argument **filepath** permettra de définir le fichier de sortie.


#### Sauvegarde automatique

Il est possible d'activer la sauvegarde automatique avec **auto_save**

```python
config.auto_save(True)
```


### Merge / Update

Fusionne un dictionnaire **dans le node courant** :
```python
config.merge({"db": {"port": 3307}}, overload=True)
```


Met à jour **une partie** :
```python
config.update("db", {"user": "root"})
```

- `overload=False` → ne remplace pas les valeurs existantes
- `overload=True` → écrase celles existantes

### Vault et données chiffrées

Le render Jinja fournis 2 méthodes pour récupérer des données chiffrées depuis un fichier vault ou un string vault_encryption

La méthode **vault** permet de récupérer des clés depuis un vault

```python
password: "{{ vault('db_password') }}"
```

Lors de l'initialisation de la config, il faudra forcément **vault_file** et **vault_password** ou **vault_keyfile**

La méthode **vault_encryption** permet de déchiffrer des clés vault_encryption

```python
api_key: "{{ vault_encryption('encrypted_api_key') }}"
```

Lors de l'initialisation de la config, il faudra forcément **vault_encryption_keyfile** ou **vault_encryption_password**

### Méthode complémentaire Jinja

#### Méthode env

La méthode **env** permet de récupérer des variables d'environnements

```python
debug: "{{ env('DEBUG', False) }}"
url: "https://{{ env('DOMAIN') }}/api"
```

## Enregistrement Jinja (filtres / tests / globals)

Tu peux enrichir l'environnement Jinja utilisé pour rendre le fichier de config.
#### register_filter(name: str, func)

Enregistre un **filtre** Jinja utilisable dans le template.

Exemple :

```python
def join_commas(items):
     return ",".join(items)
     
config.register_filter("join_commas", join_commas)
```

Utilisation dans `config.yaml` :

```jinja2
list_as_str: "{{ mylist | join_commas }}"
```

#### register_test(name: str, func)

Enregistre un **test** Jinja (ex. `is_even` pour `if x is is_even`).

Exemple :

```python
def is_even(n):
     return isinstance(n, int) and n % 2 == 0

config.register_test("is_even", is_even)
```

Utilisation :

```jinja2
{% if myvalue is is_even %}even{% endif %}
```

#### register_global(name: str, obj: Any)

Expose un objet/fonction comme **global** dans les templates Jinja (`{{ myglobal(...) }}`).

Exemple :

```python
def now():
     from datetime import datetime
     return datetime.utcnow().isoformat()

config.register_global("now", now)
```

Utilisation :

```jinja2
generated_at: "{{ now() }}"
```

### Validation de la configuration

#### Validation via schéma hiérarchique

Il est possible de vérifier une configuration à partir d'un schéma. 
Le schéma va décrire l'architecture et les prérequis des clés définis.

```python
schema = {
    "db": {
        "host": {"_type": str, "_required": True},
        "port": {"_type": int, "_min": 1, "_max": 65535}
    }
}

errors = config.validate(schema=schema)
```

#### Validation via des règles

Il est possible de vérifier une configuration à partir d'un schéma. 
Le schéma va décrire l'architecture et les prérequis des clés définis.

```python
rules = {
    r"password$": {"_min_len": 8}
    r"hostname": {"_enum": ['localhost', '127.0.0.1']}
}
errors = config.validate(rules=rules, strict=False)
```

#### Définition possible

|Règle|Pour|Description|
|---|---|---|
|`_required`|Tout|Clé obligatoire|
|`_type`|Tout|Type Python attendu|
|`_min`, `_max`|Numérique|Limites|
|`_len`, `_min_len`, `_max_len`|Chaînes|Taille|
|`_regex`|Chaînes|Validation Regex|
|`_enum`|Tout|Liste de valeurs autorisées|
|`_not`|Tout|Valeur interdite|

### Export

```python
config.export("output.yaml", type="yaml")
config.export("output.json", type="json")
config.export("output.toml", type="toml")
```

### Conversion

Ces méthodes permettent d'obtenir des formats de sortie facilement utilisables.

### to_dict()

Retourne le contenu du nœud courant (ou racine) sous forme de `dict` Python standard.

Exemple :
```python
data = config.to_dict()
# data est un dict prêt à être sérialisé
```

### to_json(indent: int = 4)

Retourne une chaîne JSON formatée du nœud courant :
```python
json_str = config.to_json()
```

### to_yaml(sort_keys: bool = True)

Retourne YAML sérialisé :
```python
yaml_str = config.to_yaml()
```

### to_toml()

Retourne TOML sérialisé (si toml est disponible) :
```python
toml_str = config.to_toml()
```

Ces méthodes n’écrivent pas sur le disque — elles renvoient des chaînes. Pour écrire un fichier, utilise `export(filepath, type=...)` ou `save()`.