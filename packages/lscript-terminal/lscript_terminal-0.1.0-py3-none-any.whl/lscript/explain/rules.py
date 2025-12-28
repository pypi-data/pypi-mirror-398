"""
Règles d'explication d'erreurs concrètes.

Ce module contient les implémentations des règles
pour les erreurs courantes.
"""

import re
from typing import List, Optional

from lscript.explain.base import ErrorRule, Explanation


# =============================================================================
# RÈGLES : Command Not Found (génériques + spécifiques)
# =============================================================================

class CommandNotFoundRule(ErrorRule):
    """Règle pour les erreurs 'command not found'."""
    
    PATTERN = re.compile(
        r"(?P<cmd>\S+):\s*(command not found|not found)|"
        r"'(?P<cmd2>[^']+)' is not recognized",
        re.IGNORECASE
    )
    
    @property
    def rule_id(self) -> str:
        return "command_not_found"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        match = self.PATTERN.search(stderr)
        cmd_name = "la commande"
        if match:
            cmd_name = match.group("cmd") or match.group("cmd2") or "la commande"
        
        return Explanation(
            title="Commande introuvable",
            message=(
                f"La commande '{cmd_name}' n'a pas été trouvée sur votre système.\n"
                f"Cela signifie que le programme n'est pas installé, "
                f"ou qu'il n'est pas dans votre PATH."
            ),
            suggestion=(
                "1. Vérifiez l'orthographe de la commande\n"
                "2. Installez le programme si nécessaire\n"
                "3. Vérifiez votre PATH avec: echo $PATH"
            ),
        )


# =============================================================================
# RÈGLES : Permission Denied
# =============================================================================

class PermissionDeniedRule(ErrorRule):
    """Règle pour les erreurs de permission."""
    
    PATTERN = re.compile(r"Permission denied|EACCES|Operation not permitted", re.IGNORECASE)
    
    @property
    def rule_id(self) -> str:
        return "permission_denied"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        return Explanation(
            title="Permission refusée",
            message=(
                "Vous n'avez pas les droits nécessaires pour cette opération.\n"
                "Cela arrive souvent avec des fichiers système ou protégés."
            ),
            suggestion=(
                "1. Utilisez sudo pour exécuter en admin: sudo <commande>\n"
                "2. Changez les permissions: chmod +x fichier\n"
                "3. Vérifiez le propriétaire du fichier: ls -la"
            ),
        )


# =============================================================================
# RÈGLES : File Not Found
# =============================================================================

class FileNotFoundRule(ErrorRule):
    """Règle pour les fichiers introuvables."""
    
    PATTERN = re.compile(
        r"No such file or directory|ENOENT|cannot stat|cannot find",
        re.IGNORECASE
    )
    
    @property
    def rule_id(self) -> str:
        return "file_not_found"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        return Explanation(
            title="Fichier ou dossier introuvable",
            message=(
                "Le fichier ou dossier spécifié n'existe pas.\n"
                "Vérifiez le chemin et l'orthographe."
            ),
            suggestion=(
                "1. Vérifiez l'orthographe du chemin\n"
                "2. Listez le contenu du dossier: ls -la (ou dir)\n"
                "3. Vérifiez votre répertoire courant: pwd\n"
                "4. Utilisez un chemin absolu si nécessaire"
            ),
        )


# =============================================================================
# RÈGLES : Syntax Error
# =============================================================================

class SyntaxErrorRule(ErrorRule):
    """Règle pour les erreurs de syntaxe."""
    
    PATTERN = re.compile(
        r"syntax error|unexpected token|parse error|unexpected end",
        re.IGNORECASE
    )
    
    @property
    def rule_id(self) -> str:
        return "syntax_error"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        return Explanation(
            title="Erreur de syntaxe",
            message=(
                "La commande contient une erreur de syntaxe.\n"
                "Le shell ne peut pas comprendre ce que vous avez écrit."
            ),
            suggestion=(
                "1. Vérifiez les guillemets: \" et '\n"
                "2. Vérifiez les parenthèses: (), {}, []\n"
                "3. Vérifiez les caractères spéciaux\n"
                "4. Utilisez \\ pour échapper les caractères spéciaux"
            ),
        )


# =============================================================================
# RÈGLES : Windows Spécifique
# =============================================================================

class WindowsCommandNotFoundRule(ErrorRule):
    """Règle spécifique pour Windows : commande non reconnue."""
    
    PATTERN = re.compile(
        r"n'est pas reconnu en tant que commande interne|"
        r"is not recognized as an internal or external command|"
        r"n'est pas reconnu comme commande|"
        r"Le terme .* n'est pas reconnu",
        re.IGNORECASE
    )
    
    @property
    def rule_id(self) -> str:
        return "windows_command_not_found"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        # Extrait le nom de la commande
        match = re.search(r"['\"]?(\S+)['\"]?\s*n'est pas reconnu|'(\S+)'.*is not recognized", stderr)
        cmd_name = "la commande"
        if match:
            cmd_name = match.group(1) or match.group(2) or "la commande"
        
        return Explanation(
            title="Commande Windows introuvable",
            message=(
                f"Windows ne reconnaît pas '{cmd_name}'.\n\n"
                "Cela peut arriver si :\n"
                "• Le programme n'est pas installé\n"
                "• Le programme n'est pas dans le PATH Windows\n"
                "• Vous utilisez une commande Linux (ls, cat, grep...)"
            ),
            suggestion=(
                "Solutions :\n"
                "1. Vérifiez l'orthographe de la commande\n"
                "2. Installez le programme si nécessaire\n"
                "3. Équivalents Windows courants :\n"
                "   • ls → dir\n"
                "   • cat → type\n"
                "   • rm → del\n"
                "   • clear → cls\n"
                "4. Vérifiez votre PATH : echo %PATH%"
            ),
        )


# =============================================================================
# RÈGLES : NPM / Node.js
# =============================================================================

class NpmNotFoundRule(ErrorRule):
    """npm/node non installé."""
    
    PATTERN = re.compile(r"npm|npx|node", re.IGNORECASE)
    PATTERN_NOT_FOUND = re.compile(r"command not found|not recognized|not found", re.IGNORECASE)
    
    @property
    def rule_id(self) -> str:
        return "npm_not_found"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return (bool(self.PATTERN.search(stderr)) and 
                bool(self.PATTERN_NOT_FOUND.search(stderr)))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        return Explanation(
            title="Node.js / npm non installé",
            message=(
                "npm (Node Package Manager) n'est pas installé sur votre système.\n"
                "npm est inclus avec Node.js et permet d'installer des packages JavaScript."
            ),
            suggestion=(
                "Installez Node.js (qui inclut npm):\n"
                "• macOS: brew install node\n"
                "• Linux: sudo apt install nodejs npm\n"
                "• Windows: https://nodejs.org\n"
                "• Ou via nvm: https://github.com/nvm-sh/nvm"
            ),
        )


class NpmInstallErrorRule(ErrorRule):
    """Erreurs npm install."""
    
    PATTERN = re.compile(r"npm ERR!|ERESOLVE|peer dep|ENOENT.*package\.json", re.IGNORECASE)
    
    @property
    def rule_id(self) -> str:
        return "npm_install_error"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        # Détection du type d'erreur npm
        if "ERESOLVE" in stderr or "peer dep" in stderr.lower():
            return Explanation(
                title="Conflit de dépendances npm",
                message=(
                    "npm n'arrive pas à résoudre les dépendances de votre projet.\n"
                    "Certains packages ont des versions incompatibles entre elles."
                ),
                suggestion=(
                    "Solutions:\n"
                    "1. npm install --legacy-peer-deps\n"
                    "2. npm install --force\n"
                    "3. Supprimez node_modules et package-lock.json, puis réessayez\n"
                    "4. Vérifiez les versions dans package.json"
                ),
            )
        elif "package.json" in stderr.lower():
            return Explanation(
                title="package.json introuvable",
                message=(
                    "npm ne trouve pas de fichier package.json dans ce dossier.\n"
                    "Ce fichier définit les dépendances de votre projet Node.js."
                ),
                suggestion=(
                    "Solutions:\n"
                    "1. Vérifiez que vous êtes dans le bon dossier\n"
                    "2. Créez un nouveau projet: npm init -y\n"
                    "3. Ou clonez un projet existant avec son package.json"
                ),
            )
        else:
            return Explanation(
                title="Erreur npm",
                message="Une erreur s'est produite lors de l'exécution de npm.",
                suggestion=(
                    "1. Lisez le message d'erreur complet\n"
                    "2. Essayez: npm cache clean --force\n"
                    "3. Supprimez node_modules et réessayez\n"
                    "4. Vérifiez votre connexion internet"
                ),
            )


# =============================================================================
# RÈGLES : Git
# =============================================================================

class GitNotFoundRule(ErrorRule):
    """Git non installé."""
    
    PATTERN = re.compile(r"git.*not found|git.*not recognized", re.IGNORECASE)
    
    @property
    def rule_id(self) -> str:
        return "git_not_found"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        return Explanation(
            title="Git non installé",
            message=(
                "Git n'est pas installé sur votre système.\n"
                "Git est un système de contrôle de version essentiel pour le développement."
            ),
            suggestion=(
                "Installez Git:\n"
                "• macOS: brew install git (ou Xcode Command Line Tools)\n"
                "• Linux: sudo apt install git\n"
                "• Windows: https://git-scm.com/download/win"
            ),
        )


class GitNotRepoRule(ErrorRule):
    """Pas un dépôt git."""
    
    PATTERN = re.compile(r"not a git repository|fatal:.*\.git", re.IGNORECASE)
    
    @property
    def rule_id(self) -> str:
        return "git_not_repo"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        return Explanation(
            title="Pas un dépôt Git",
            message=(
                "Ce dossier n'est pas un dépôt Git.\n"
                "Les commandes git ne fonctionnent que dans un dépôt initialisé."
            ),
            suggestion=(
                "Solutions:\n"
                "1. Initialisez un nouveau dépôt: git init\n"
                "2. Clonez un dépôt existant: git clone <url>\n"
                "3. Naviguez vers un dossier contenant un dépôt git"
            ),
        )


class GitMergeConflictRule(ErrorRule):
    """Conflit de merge git."""
    
    PATTERN = re.compile(r"CONFLICT|merge conflict|Automatic merge failed", re.IGNORECASE)
    
    @property
    def rule_id(self) -> str:
        return "git_merge_conflict"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        return Explanation(
            title="Conflit de fusion Git",
            message=(
                "Git n'a pas pu fusionner automatiquement les modifications.\n"
                "Vous devez résoudre manuellement les conflits dans les fichiers concernés."
            ),
            suggestion=(
                "Étapes pour résoudre:\n"
                "1. Ouvrez les fichiers en conflit (marqués par <<<<<<)\n"
                "2. Choisissez les modifications à garder\n"
                "3. Supprimez les marqueurs de conflit\n"
                "4. git add <fichiers>\n"
                "5. git commit"
            ),
        )


class GitPushRejectedRule(ErrorRule):
    """Push git rejeté."""
    
    PATTERN = re.compile(r"rejected|non-fast-forward|fetch first|pull.*before push", re.IGNORECASE)
    
    @property
    def rule_id(self) -> str:
        return "git_push_rejected"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return "git" in stderr.lower() and bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        return Explanation(
            title="Push Git rejeté",
            message=(
                "Le serveur a rejeté votre push.\n"
                "Le dépôt distant contient des commits que vous n'avez pas en local."
            ),
            suggestion=(
                "Solutions:\n"
                "1. git pull --rebase origin <branche>\n"
                "2. Résolvez les conflits si nécessaire\n"
                "3. git push à nouveau\n\n"
                "Ou si vous voulez forcer (⚠️ dangereux):\n"
                "git push --force-with-lease"
            ),
        )


# =============================================================================
# RÈGLES : Python
# =============================================================================

class PythonNotFoundRule(ErrorRule):
    """Python non installé."""
    
    PATTERN = re.compile(r"python.*not found|python.*not recognized|pip.*not found", re.IGNORECASE)
    
    @property
    def rule_id(self) -> str:
        return "python_not_found"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        return Explanation(
            title="Python non installé",
            message=(
                "Python n'est pas installé ou accessible sur votre système.\n"
                "Python est un langage de programmation très répandu."
            ),
            suggestion=(
                "Installez Python:\n"
                "• macOS: brew install python3\n"
                "• Linux: sudo apt install python3 python3-pip\n"
                "• Windows: https://python.org\n\n"
                "Astuce: utilisez 'python3' au lieu de 'python' sur Linux/macOS"
            ),
        )


class PythonModuleNotFoundRule(ErrorRule):
    """Module Python introuvable."""
    
    PATTERN = re.compile(r"ModuleNotFoundError|No module named|ImportError", re.IGNORECASE)
    
    @property
    def rule_id(self) -> str:
        return "python_module_not_found"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        # Essaie d'extraire le nom du module
        match = re.search(r"No module named ['\"]?(\w+)['\"]?", stderr)
        module_name = match.group(1) if match else "le module"
        
        return Explanation(
            title=f"Module Python '{module_name}' introuvable",
            message=(
                f"Le module Python '{module_name}' n'est pas installé dans votre environnement.\n"
                "Python ne peut pas importer un module qui n'existe pas."
            ),
            suggestion=(
                f"Installez le module:\n"
                f"  pip install {module_name}\n\n"
                "Si vous utilisez un environnement virtuel, vérifiez qu'il est activé:\n"
                "  source venv/bin/activate  (Linux/macOS)\n"
                "  venv\\Scripts\\activate    (Windows)"
            ),
        )


class PythonSyntaxErrorRule(ErrorRule):
    """Erreur de syntaxe Python."""
    
    PATTERN = re.compile(r"SyntaxError:|IndentationError:|TabError:", re.IGNORECASE)
    
    @property
    def rule_id(self) -> str:
        return "python_syntax_error"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        if "IndentationError" in stderr or "TabError" in stderr:
            return Explanation(
                title="Erreur d'indentation Python",
                message=(
                    "Votre code Python a un problème d'indentation.\n"
                    "Python utilise l'indentation pour définir les blocs de code."
                ),
                suggestion=(
                    "1. Utilisez des espaces, pas des tabs (4 espaces recommandés)\n"
                    "2. Ne mélangez pas tabs et espaces\n"
                    "3. Vérifiez l'alignement après if, for, def, class\n"
                    "4. Configurez votre éditeur pour afficher les espaces"
                ),
            )
        else:
            return Explanation(
                title="Erreur de syntaxe Python",
                message=(
                    "Votre code Python contient une erreur de syntaxe.\n"
                    "Python ne peut pas exécuter du code mal formé."
                ),
                suggestion=(
                    "Erreurs courantes:\n"
                    "1. Oubli de ':' après if, for, def, class\n"
                    "2. Parenthèses non fermées ()\n"
                    "3. Guillemets non fermés \"\" ou ''\n"
                    "4. Mot-clé mal orthographié (True, False, None)"
                ),
            )


# =============================================================================
# RÈGLES : Docker
# =============================================================================

class DockerNotFoundRule(ErrorRule):
    """Docker non installé."""
    
    PATTERN = re.compile(r"docker.*not found|docker.*not recognized", re.IGNORECASE)
    
    @property
    def rule_id(self) -> str:
        return "docker_not_found"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        return Explanation(
            title="Docker non installé",
            message=(
                "Docker n'est pas installé sur votre système.\n"
                "Docker permet d'exécuter des applications dans des conteneurs isolés."
            ),
            suggestion=(
                "Installez Docker:\n"
                "• macOS/Windows: Docker Desktop depuis https://docker.com\n"
                "• Linux: sudo apt install docker.io\n\n"
                "N'oubliez pas de démarrer le service Docker après l'installation."
            ),
        )


class DockerDaemonNotRunningRule(ErrorRule):
    """Le daemon Docker n'est pas en cours d'exécution."""
    
    PATTERN = re.compile(r"Cannot connect to the Docker daemon|docker daemon|Is the docker daemon running", re.IGNORECASE)
    
    @property
    def rule_id(self) -> str:
        return "docker_daemon_not_running"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        return Explanation(
            title="Docker daemon non démarré",
            message=(
                "Le service Docker n'est pas en cours d'exécution.\n"
                "Docker doit être démarré avant de pouvoir exécuter des conteneurs."
            ),
            suggestion=(
                "Démarrez Docker:\n"
                "• macOS/Windows: Lancez l'application Docker Desktop\n"
                "• Linux: sudo systemctl start docker\n\n"
                "Pour démarrer automatiquement au boot:\n"
                "  sudo systemctl enable docker"
            ),
        )


# =============================================================================
# RÈGLES : Réseau
# =============================================================================

class NetworkUnreachableRule(ErrorRule):
    """Réseau inaccessible."""
    
    PATTERN = re.compile(
        r"Network is unreachable|Connection refused|ECONNREFUSED|"
        r"Could not resolve host|Name or service not known|ETIMEDOUT",
        re.IGNORECASE
    )
    
    @property
    def rule_id(self) -> str:
        return "network_error"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        if "resolve" in stderr.lower() or "Name or service" in stderr:
            return Explanation(
                title="Résolution DNS échouée",
                message=(
                    "Le nom de domaine n'a pas pu être résolu en adresse IP.\n"
                    "Soit le domaine n'existe pas, soit votre DNS ne fonctionne pas."
                ),
                suggestion=(
                    "1. Vérifiez l'orthographe du domaine\n"
                    "2. Testez votre DNS: ping google.com\n"
                    "3. Essayez un autre DNS (8.8.8.8 ou 1.1.1.1)\n"
                    "4. Vérifiez votre connexion internet"
                ),
            )
        elif "refused" in stderr.lower():
            return Explanation(
                title="Connexion refusée",
                message=(
                    "Le serveur refuse la connexion.\n"
                    "Le service n'est peut-être pas démarré ou le port est bloqué."
                ),
                suggestion=(
                    "1. Vérifiez que le serveur est démarré\n"
                    "2. Vérifiez le numéro de port\n"
                    "3. Vérifiez le pare-feu\n"
                    "4. Pour un serveur local: npm start, python -m http.server, etc."
                ),
            )
        else:
            return Explanation(
                title="Problème de connexion réseau",
                message=(
                    "Impossible d'établir une connexion réseau.\n"
                    "Vérifiez votre connexion internet."
                ),
                suggestion=(
                    "1. Vérifiez votre connexion WiFi/Ethernet\n"
                    "2. Testez avec: ping 8.8.8.8\n"
                    "3. Redémarrez votre routeur si nécessaire\n"
                    "4. Désactivez le VPN temporairement"
                ),
            )


class PortInUseRule(ErrorRule):
    """Port déjà utilisé."""
    
    PATTERN = re.compile(r"Address already in use|EADDRINUSE|port.*already|already.*port", re.IGNORECASE)
    
    @property
    def rule_id(self) -> str:
        return "port_in_use"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        return Explanation(
            title="Port déjà utilisé",
            message=(
                "Le port que vous essayez d'utiliser est déjà pris par un autre programme.\n"
                "Un seul programme peut écouter sur un port à la fois."
            ),
            suggestion=(
                "Trouvez le programme utilisant le port:\n"
                "• Linux/macOS: lsof -i :<port>\n"
                "• Windows: netstat -ano | findstr :<port>\n\n"
                "Solutions:\n"
                "1. Arrêtez le programme qui utilise le port\n"
                "2. Utilisez un autre port (ex: PORT=3001 npm start)"
            ),
        )


# =============================================================================
# RÈGLES : Disque
# =============================================================================

class DiskFullRule(ErrorRule):
    """Disque plein."""
    
    PATTERN = re.compile(r"No space left|ENOSPC|Disk quota exceeded", re.IGNORECASE)
    
    @property
    def rule_id(self) -> str:
        return "disk_full"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return bool(self.PATTERN.search(stderr))
    
    def explain(self, stderr: str, command: str) -> Explanation:
        return Explanation(
            title="Disque plein",
            message=(
                "Il n'y a plus d'espace disponible sur votre disque.\n"
                "Vous devez libérer de l'espace avant de pouvoir continuer."
            ),
            suggestion=(
                "Libérez de l'espace:\n"
                "1. Vérifiez l'espace: df -h (Linux/macOS) ou Propriétés (Windows)\n"
                "2. Trouvez les gros fichiers: du -sh * | sort -h\n"
                "3. Videz la corbeille\n"
                "4. Nettoyez les caches:\n"
                "   • npm cache clean --force\n"
                "   • docker system prune\n"
                "   • pip cache purge"
            ),
        )


# =============================================================================
# RÈGLE FALLBACK : Erreur Générique
# =============================================================================

class FallbackRule(ErrorRule):
    """
    Règle de secours quand aucune autre règle ne matche.
    """
    
    @property
    def rule_id(self) -> str:
        return "fallback"
    
    def match(self, stderr: str, return_code: int) -> bool:
        return True
    
    def explain(self, stderr: str, command: str) -> Explanation:
        return Explanation(
            title="Erreur non reconnue",
            message=(
                "LScript n'a pas reconnu cette erreur spécifique.\n"
                "Consultez le message d'erreur ci-dessus pour plus de détails."
            ),
            suggestion=(
                "1. Lisez attentivement le message d'erreur\n"
                "2. Recherchez le message sur Google ou Stack Overflow\n"
                "3. Consultez la documentation: man <commande> ou --help\n"
                "4. Demandez de l'aide sur Discord ou GitHub"
            ),
        )


# =============================================================================
# REGISTRY : Registre des règles
# =============================================================================

class RuleRegistry:
    """
    Registre des règles d'explication.
    
    Gère une liste ordonnée de règles et trouve la première
    qui matche une erreur donnée.
    """
    
    def __init__(self):
        self._rules: List[ErrorRule] = []
        self._fallback: Optional[ErrorRule] = None
    
    def register(self, rule: ErrorRule) -> None:
        """Enregistre une règle."""
        self._rules.append(rule)
    
    def set_fallback(self, rule: ErrorRule) -> None:
        """Définit la règle de secours."""
        self._fallback = rule
    
    def find_match(self, stderr: str, return_code: int) -> Optional[ErrorRule]:
        """
        Trouve la première règle qui matche.
        """
        for rule in self._rules:
            if rule.match(stderr, return_code):
                return rule
        
        return self._fallback
    
    @property
    def rule_count(self) -> int:
        """Nombre de règles enregistrées (sans fallback)."""
        return len(self._rules)


def create_default_registry() -> RuleRegistry:
    """
    Crée un registre avec les règles par défaut.
    
    Les règles sont ordonnées par spécificité:
    - Plus une règle est spécifique, plus elle est prioritaire
    - Les règles génériques sont testées en dernier
    """
    registry = RuleRegistry()
    
    # === Règles spécifiques (haute priorité) ===
    # npm
    registry.register(NpmNotFoundRule())
    registry.register(NpmInstallErrorRule())
    
    # git
    registry.register(GitNotFoundRule())
    registry.register(GitNotRepoRule())
    registry.register(GitMergeConflictRule())
    registry.register(GitPushRejectedRule())
    
    # python
    registry.register(PythonNotFoundRule())
    registry.register(PythonModuleNotFoundRule())
    registry.register(PythonSyntaxErrorRule())
    
    # docker
    registry.register(DockerNotFoundRule())
    registry.register(DockerDaemonNotRunningRule())
    
    # réseau
    registry.register(NetworkUnreachableRule())
    registry.register(PortInUseRule())
    
    # disque
    registry.register(DiskFullRule())
    
    # windows spécifique
    registry.register(WindowsCommandNotFoundRule())
    
    # === Règles génériques (basse priorité) ===
    registry.register(CommandNotFoundRule())
    registry.register(PermissionDeniedRule())
    registry.register(FileNotFoundRule())
    registry.register(SyntaxErrorRule())
    
    # Fallback
    registry.set_fallback(FallbackRule())
    
    return registry
