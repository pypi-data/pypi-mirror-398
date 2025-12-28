"""
Shell interactif LScript.

Boucle REPL qui lit les commandes, les exécute
et affiche des explications humaines en cas d'erreur.

Supporte deux modes d'affichage:
- Rich (si installé) → UI moderne et colorée
- Fallback (stdlib) → Fonctionne partout
"""

import os
import sys

from lscript import __version__
from lscript.runner import run_command, CommandResult
from lscript.explain import create_default_registry, Explanation
from lscript.plugins import PluginManager

# Import conditionnel de readline (historique des commandes)
try:
    import readline  # noqa: F401
except ImportError:
    pass

# Détection de Rich pour UI moderne
try:
    from rich.console import Console
    from lscript.ui.formatter import ErrorFormatter, PromptFormatter
    from lscript.ui.theme import DEFAULT_THEME
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class LScriptShell:
    """
    Shell interactif LScript.
    
    Fournit une boucle REPL qui:
    1. Lit les commandes utilisateur
    2. Les exécute via subprocess
    3. Analyse les erreurs
    4. Affiche des explications humaines
    
    Utilise Rich si disponible, sinon fallback stdlib.
    """
    
    def __init__(self, use_rich: bool = True):
        """
        Initialise le shell.
        
        Args:
            use_rich: Utiliser Rich si disponible (True par défaut)
        """
        # Initialisation Plugins
        self.plugin_manager = PluginManager()
        self.plugin_manager.load_installed_plugins()
        
        # Initialisation Règles
        self.registry = create_default_registry()
        
        # Ajout des règles plugins au registre
        for rule in self.plugin_manager.get_all_rules():
            self.registry.register(rule)
            
        self._running = False
        self._last_exit_code = 0
        
        # Configuration UI
        self._use_rich = use_rich and RICH_AVAILABLE
        if self._use_rich:
            self._console = Console()
            self._error_fmt = ErrorFormatter(self._console)
            self._prompt_fmt = PromptFormatter(self._console)
    
    def run(self) -> int:
        """
        Lance la boucle interactive principale.
        
        Returns:
            Code de sortie (0 pour succès)
        """
        self._running = True
        self._print_welcome()
        
        while self._running:
            try:
                command = self._read_command()
                
                if command is None:
                    break
                
                self._execute(command)
                
            except KeyboardInterrupt:
                print("\n^C")
                self._last_exit_code = 130
                continue
        
        self._print_goodbye()
        return 0
    
    def _read_command(self) -> str:
        """Lit une commande depuis stdin."""
        try:
            self._print_prompt()
            command = input().strip()
            return command
        except EOFError:
            return None
    
    def _print_prompt(self) -> None:
        """Affiche le prompt."""
        cwd = self._get_short_cwd()
        last_success = (self._last_exit_code == 0)
        
        if self._use_rich:
            self._prompt_fmt.print_prompt(cwd, last_success)
        else:
            indicator = "❯" if last_success else "✗"
            print(f"{cwd} {indicator} ", end="", flush=True)
    
    def _get_short_cwd(self) -> str:
        """Retourne le répertoire courant raccourci."""
        cwd = os.getcwd()
        home = os.path.expanduser("~")
        if cwd.startswith(home):
            cwd = "~" + cwd[len(home):]
        if len(cwd) > 40:
            cwd = "..." + cwd[-37:]
        return cwd
    
    def _execute(self, command: str) -> None:
        """Exécute une commande."""
        if not command:
            return
        
        if self._handle_builtin(command):
            return
        
        if command.startswith("cd ") or command == "cd":
            self._handle_cd(command)
            return
        
        result = run_command(command)
        self._last_exit_code = result.return_code
        
        if result.success:
            self._display_success(result)
        else:
            self._display_error(result)
    
    def _handle_builtin(self, command: str) -> bool:
        """Gère les commandes internes."""
        cmd = command.lower().split()[0] if command.split() else ""
        
        if cmd in ("exit", "quit"):
            self._running = False
            return True
        
        if cmd == "help":
            self._print_help()
            return True
        
        if cmd in ("clear", "cls"):
            os.system("clear" if os.name != "nt" else "cls")
            return True
        
        return False
    
    def _handle_cd(self, command: str) -> None:
        """Gère la commande cd."""
        parts = command.split(maxsplit=1)
        target = os.path.expanduser(parts[1] if len(parts) > 1 else "~")
        
        try:
            os.chdir(target)
            self._last_exit_code = 0
        except FileNotFoundError:
            self._print_error(f"cd: {target}: Aucun fichier ou dossier de ce type")
            self._last_exit_code = 1
        except PermissionError:
            self._print_error(f"cd: {target}: Permission refusée")
            self._last_exit_code = 1
        except Exception as e:
            self._print_error(f"cd: {e}")
            self._last_exit_code = 1
    
    def _display_success(self, result: CommandResult) -> None:
        """Affiche le résultat d'une commande réussie."""
        if self._use_rich:
            self._error_fmt.display_success(result)
        elif result.stdout:
            print(result.stdout, end="")
    
    def _display_error(self, result: CommandResult) -> None:
        """Affiche une erreur avec explication."""
        rule = self.registry.find_match(result.stderr, result.return_code)
        
        if rule:
            explanation = rule.explain(result.stderr, result.command)
            
            if self._use_rich:
                self._error_fmt.display_error(result, explanation)
            else:
                self._display_error_fallback(result, explanation)
    
    def _display_error_fallback(self, result: CommandResult, exp: Explanation) -> None:
        """Affichage sans Rich (fallback stdlib)."""
        if result.stderr:
            for line in result.stderr.strip().split("\n")[:10]:
                print(f"  {line}")
        
        print()
        sep = "─" * 50
        
        print(f"╭{sep}╮")
        print(f"│ ❌ Erreur Détectée")
        print(f"│ commande: {result.command}")
        print(f"│ code: {result.return_code}")
        print(f"╰{sep}╯")
        print()
        
        print(f"╭{sep}╮")
        print(f"│ 🧠 {exp.title}")
        print(f"│")
        for line in exp.message.split("\n"):
            print(f"│ {line}")
        print(f"╰{sep}╯")
        print()
        
        print(f"╭{sep}╮")
        print(f"│ ✅ Solution Suggérée")
        print(f"│")
        for line in exp.suggestion.split("\n"):
            print(f"│ {line}")
        print(f"╰{sep}╯")
        print()
    
    def _print_error(self, message: str) -> None:
        """Affiche un message d'erreur simple."""
        if self._use_rich:
            self._console.print(f"[red]{message}[/red]")
        else:
            print(message)
    
    def _print_welcome(self) -> None:
        """Affiche le message de bienvenue."""
        if self._use_rich:
            self._prompt_fmt.print_welcome(__version__, self.registry.rule_count)
        else:
            print()
            print(f"🚀 LScript v{__version__} — Terminal intelligent orienté humain")
            print("Tapez une commande. Les erreurs seront expliquées.")
            print("Tapez 'exit' ou Ctrl+D pour quitter.")
            print()
    
    def _print_goodbye(self) -> None:
        """Affiche le message de fin."""
        if self._use_rich:
            self._prompt_fmt.print_goodbye()
        else:
            print()
            print("👋 À bientôt !")
    
    def _print_help(self) -> None:
        """Affiche l'aide."""
        if self._use_rich:
            self._prompt_fmt.print_help(__version__, self.registry.rule_count)
        else:
            print()
            print(f"LScript v{__version__} — Terminal intelligent orienté humain")
            print()
            print("Commandes internes:")
            print("  exit, quit  — Quitter LScript")
            print("  help        — Afficher cette aide")
            print("  clear, cls  — Effacer l'écran")
            print("  cd <chemin> — Changer de répertoire")
            print()
            print(f"Règles chargées: {self.registry.rule_count}")
            print()
