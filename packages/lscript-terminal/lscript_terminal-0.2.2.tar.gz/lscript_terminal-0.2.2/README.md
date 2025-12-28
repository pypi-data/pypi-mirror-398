# 🚀 LScript

[![PyPI version](https://badge.fury.io/py/lscript.svg)](https://pypi.org/project/lscript/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## Pourquoi LScript existe

> **Le terminal n'a jamais été conçu pour être compris.**

Quand une commande échoue, vous recevez un message d'erreur cryptique. `ENOENT`, `command not found`, `permission denied`... Des mots qui ne vous aident pas. Vous copiez-collez sur Google, vous perdez 10 minutes, vous vous sentez frustré.

**LScript change ça.**

Au lieu d'un message technique incompréhensible, LScript vous explique :

- 🧠 **Ce qui s'est passé** — en langage humain, pas en jargon
- ✅ **Comment le résoudre** — avec des actions concrètes, pas des théories

LScript est un terminal qui vous accompagne. Pas un outil qui vous juge.

Conçu pour les développeurs qui apprennent, et ceux qui en ont marre de perdre du temps sur des erreurs triviales.

## 🎯 Pour qui ?

- Développeurs **débutants** qui veulent comprendre leurs erreurs
- Développeurs **intermédiaires** qui veulent gagner du temps
- **Formateurs** qui veulent un terminal pédagogique

## 📦 Installation

```bash
# Installation depuis PyPI
pip install lscript

# Avec UI moderne (recommandé)
pip install lscript[ui]

# Ou depuis les sources
git clone https://github.com/lscript/lscript.git
cd lscript
pip install -e ".[ui]"
```

## 🚀 Utilisation

```bash
# Lancer LScript
lscript

# Ou via Python
python -m lscript
```

## 💡 Exemple

```
🚀 LScript v0.1.0
Terminal intelligent orienté humain
19 règles chargées • Tapez 'help' pour l'aide

~ ❯ npm install

  bash: npm: command not found

╭─ ❌ Erreur Détectée ────────────────────────────────╮
│ commande npm install                                │
│ code 127                                            │
╰─────────────────────────────────────────────────────╯
╭─ 🧠 Explication ────────────────────────────────────╮
│ Node.js / npm non installé                          │
│                                                     │
│ npm (Node Package Manager) n'est pas installé sur  │
│ votre système. npm est inclus avec Node.js.        │
╰─────────────────────────────────────────────────────╯
╭─ ✅ Solution Suggérée ──────────────────────────────╮
│ Installez Node.js (qui inclut npm):                │
│ • macOS: brew install node                         │
│ • Linux: sudo apt install nodejs npm               │
│ • Windows: https://nodejs.org                      │
╰─────────────────────────────────────────────────────╯
```

## 📋 Règles Supportées

### Génériques

| Règle               | Description          |
| ------------------- | -------------------- |
| `command_not_found` | Commande inexistante |
| `permission_denied` | Droits insuffisants  |
| `file_not_found`    | Fichier introuvable  |
| `syntax_error`      | Erreur de syntaxe    |

### npm / Node.js

| Règle               | Description          |
| ------------------- | -------------------- |
| `npm_not_found`     | Node.js non installé |
| `npm_install_error` | Erreurs npm install  |

### Git

| Règle                | Description       |
| -------------------- | ----------------- |
| `git_not_found`      | Git non installé  |
| `git_not_repo`       | Pas un dépôt Git  |
| `git_merge_conflict` | Conflit de fusion |
| `git_push_rejected`  | Push rejeté       |

### Python

| Règle                     | Description         |
| ------------------------- | ------------------- |
| `python_not_found`        | Python non installé |
| `python_module_not_found` | Module manquant     |
| `python_syntax_error`     | Erreur de syntaxe   |

### Docker

| Règle                       | Description         |
| --------------------------- | ------------------- |
| `docker_not_found`          | Docker non installé |
| `docker_daemon_not_running` | Daemon arrêté       |

### Réseau & Système

| Règle           | Description           |
| --------------- | --------------------- |
| `network_error` | Problème de connexion |
| `port_in_use`   | Port déjà utilisé     |
| `disk_full`     | Disque plein          |

## 🏗️ Architecture

```
lscript/
├── cli.py           # Point d'entrée CLI
├── shell.py         # Boucle REPL
├── runner.py        # Exécution subprocess
├── plugins.py       # Système de plugins
├── explain/         # CORE MÉTIER
│   ├── base.py      # Classes abstraites
│   └── rules.py     # 19 règles intégrées
└── ui/              # COUCHE UI (optionnelle)
    ├── theme.py     # 5 thèmes
    └── formatter.py # Affichage Rich
```

## 🔌 Créer un plugin

```python
from lscript.plugins import LScriptPlugin, PluginInfo
from lscript.explain.base import ErrorRule, Explanation

class MyPlugin(LScriptPlugin):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            id="my-plugin",
            name="Mon Plugin",
            version="1.0.0",
        )

    def get_rules(self) -> list:
        return [MyCustomRule()]
```

## 🎨 Thèmes

| Thème     | Description          | Premium |
| --------- | -------------------- | ------- |
| `default` | Sobre et pédagogique | ❌      |
| `dark`    | Mode sombre          | ✅      |
| `light`   | Mode clair           | ✅      |
| `hacker`  | Terminal vert        | ✅      |
| `dracula` | Thème Dracula        | ✅      |

## 🤝 Contribuer

Les contributions sont les bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 Licence

MIT License - Voir [LICENSE](LICENSE)

---

**Fait avec ❤️ pour les développeurs** | [lscript.fr](https://lscript.fr)
