# Master DAC

Code permettant de gérer les configurations des machines des étudiants DAC (packages python, jeux de données)

## Pour publier sur pypi

### Configuration initiale (à faire une fois)

Éditer le fichier de configuration Hatch:
- **macOS**: `~/Library/Application Support/hatch/config.toml`
- **Linux**: `~/.config/hatch/config.toml`
- **Windows**: `%USERPROFILE%\AppData\Local\hatch\config.toml`

Ajouter:

```toml
[publish]

[publish.index]

[publish.index.repos.su-master-mind]
url = "https://upload.pypi.org/legacy/"
user = "__token__"
auth = "pypi-YOUR_PROJECT_SPECIFIC_TOKEN_HERE"
```

Remplacer `YOUR_PROJECT_SPECIFIC_TOKEN_HERE` par votre token PyPI spécifique au projet.

### Publier une nouvelle version

Le projet utilise le versionnage calendaire (CalVer) au format `YYYY.MM.DD.N` où N s'incrémente pour les versions multiples le même jour.

```sh
# Mettre à jour la version à la date du jour (incrémente N automatiquement)
hatch version release

# Vérifier la version actuelle
hatch version

# Build
hatch build

# Publish using the configured repository
hatch publish -r su-master-mind
```

Note:
- La commande `hatch version release` met à jour automatiquement `master_mind/__version__.py`
- Le `-r su-master-mind` est nécessaire pour utiliser le dépôt configuré ci-dessus
