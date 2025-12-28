"""
Formateur d'affichage Rich pour LScript.

Ce module transforme les données du core (Explanation, CommandResult)
en affichage Rich élégant et pédagogique.

Architecture:
- Ne modifie PAS le core (explain, runner)
- Consomme les dataclasses existantes
- Produit un affichage Rich
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

from lscript.runner import CommandResult
from lscript.explain.base import Explanation
from lscript.ui.theme import Theme, DEFAULT_THEME
import re

# Indices pour les fonctionnalités Premium (Shadow Detection)
PREMIUM_HINTS = {
    r"Microsoft Store": "LScript Pro gère spécifiquement le piège des alias Windows Python.",
    r"detached HEAD": "LScript Pro explique comment sauver vos commits perdus.",
    r"externally-managed-environment": "LScript Pro explique la PEP 668 et les environnements virtuels.",
}


class ErrorFormatter:
    """
    Formate les erreurs pour un affichage Rich.
    
    Affiche systématiquement 3 sections:
    ❌ Erreur détectée (commande + code)
    🧠 Explication humaine
    ✅ Action conseillée
    
    Design:
    - Sobriété (pas de surcharge visuelle)
    - Lisibilité (hiérarchie claire)
    - Pédagogie (ton rassurant)
    """
    
    def __init__(self, console: Console = None, theme: Theme = None):
        """
        Initialise le formatter.
        
        Args:
            console: Console Rich (créée si None)
            theme: Thème de couleurs (défaut si None)
        """
        self.console = console or Console()
        self.theme = theme or DEFAULT_THEME
    
    def display_error(
        self, 
        result: CommandResult, 
        explanation: Explanation
    ) -> None:
        """
        Affiche une erreur avec son explication.
        
        Args:
            result: Résultat de la commande échouée
            explanation: Explication générée par le moteur de règles
        """
        # Espace avant l'affichage
        self.console.print()
        
        # stderr brut (discret, pour référence)
        if result.stderr:
            self._display_stderr(result.stderr)
        
        # ❌ Erreur détectée
        self._display_error_panel(result)
        
        # 🧠 Explication
        self._display_explanation_panel(explanation)
        
        # ✅ Solution
        self._display_solution_panel(explanation)
        
        # 💡 Premium Hint (Shadow Detection)
        self._display_premium_hint(result.stderr)
    
    def display_success(self, result: CommandResult) -> None:
        """
        Affiche le résultat d'une commande réussie.
        
        Simple passthrough du stdout, sans décoration.
        """
        if result.stdout:
            self.console.print(result.stdout, end="")
    
    def _display_stderr(self, stderr: str) -> None:
        """Affiche le stderr brut de manière discrète."""
        lines = stderr.strip().split("\n")
        # Limite à 10 lignes pour la lisibilité
        if len(lines) > 10:
            lines = lines[:10]
            lines.append(f"  ... ({len(stderr.strip().split(chr(10))) - 10} lignes supplémentaires)")
        
        for line in lines:
            self.console.print(f"  {line}", style=self.theme.muted)
        
        self.console.print()
    
    def _display_error_panel(self, result: CommandResult) -> None:
        """Affiche le panel d'erreur - ton rassurant."""
        content = Text()
        content.append("Commande ", style="dim")
        content.append(result.command, style=self.theme.code)
        content.append("\n")
        content.append("Code de sortie ", style="dim")
        content.append(str(result.return_code), style=self.theme.error)
        
        panel = Panel(
            content,
            title="[bold]❌ Oups, quelque chose n'a pas marché[/bold]",
            title_align="left",
            border_style=self.theme.border_error,
            box=box.ROUNDED,
            padding=(0, 1),
        )
        self.console.print(panel)
    
    def _display_explanation_panel(self, explanation: Explanation) -> None:
        """Affiche le panel d'explication - ton pédagogique."""
        content = Text()
        # Titre de l'erreur en gras cyan
        content.append(explanation.title, style="bold " + self.theme.info)
        content.append("\n\n")
        # Message explicatif
        content.append(explanation.message)
        
        panel = Panel(
            content,
            title="[bold]🧠 Voici ce qui s'est passé[/bold]",
            title_align="left",
            border_style=self.theme.border_info,
            box=box.ROUNDED,
            padding=(0, 1),
        )
        self.console.print(panel)
    
    def _display_solution_panel(self, explanation: Explanation) -> None:
        """Affiche le panel de solution - ton encourageant."""
        content = Text()
        content.append(explanation.suggestion)
        
        panel = Panel(
            content,
            title="[bold]✅ Comment résoudre ça[/bold]",
            title_align="left",
            border_style=self.theme.border_success,
            box=box.ROUNDED,
            padding=(0, 1),
        )
        self.console.print(panel)
        self.console.print()
    
    def _display_premium_hint(self, stderr: str) -> None:
        """Affiche un indice discret pour les fonctionnalités Pro."""
        if not stderr:
            return
            
        for pattern, hint in PREMIUM_HINTS.items():
            if re.search(pattern, stderr, re.IGNORECASE):
                content = Text()
                content.append("💡 Le Saviez-vous ? ", style="bold yellow")
                content.append(hint + "\n")
                content.append("👉 ", style="dim")
                # Lien cliquable si supporté par le terminal
                content.append("Découvrir LScript Pro", style="blue underline link https://lscript.fr/pro")
                
                panel = Panel(
                    content,
                    border_style="dim white",
                    box=box.ROUNDED,
                    padding=(0, 1),
                )
                self.console.print(panel)
                self.console.print()
                break


class PromptFormatter:
    """
    Formate le prompt LScript avec Rich.
    
    Affiche:
    - Répertoire courant (raccourci)
    - Indicateur de statut coloré
    """
    
    def __init__(self, console: Console = None, theme: Theme = None):
        self.console = console or Console()
        self.theme = theme or DEFAULT_THEME
    
    def print_prompt(self, cwd: str, last_success: bool) -> None:
        """
        Affiche le prompt.
        
        Args:
            cwd: Répertoire courant
            last_success: True si dernière commande OK
        """
        prompt = Text()
        prompt.append(cwd, style="bold " + self.theme.info)
        prompt.append(" ")
        
        if last_success:
            prompt.append("❯", style=self.theme.prompt_ok)
        else:
            prompt.append("✗", style=self.theme.prompt_error)
        
        prompt.append(" ")
        self.console.print(prompt, end="")
    
    def print_welcome(self, version: str, rule_count: int) -> None:
        """Affiche le message de bienvenue."""
        self.console.print()
        self.console.print(
            f"[bold {self.theme.info}]🚀 LScript[/] v{version}",
            highlight=False,
        )
        self.console.print(
            "[dim]Terminal intelligent orienté humain[/dim]"
        )
        self.console.print(
            f"[dim]{rule_count} règles chargées • Tapez 'help' pour l'aide[/dim]"
        )
        self.console.print()
    
    def print_goodbye(self) -> None:
        """Affiche le message de sortie."""
        self.console.print()
        self.console.print("[dim]👋 À bientôt ![/dim]")
    
    def print_help(self, version: str, rule_count: int) -> None:
        """Affiche l'aide."""
        self.console.print()
        self.console.print(
            f"[bold {self.theme.info}]LScript[/] v{version}",
            highlight=False,
        )
        self.console.print()
        self.console.print("[bold]Commandes internes:[/bold]")
        self.console.print(f"  [{self.theme.info}]exit, quit[/]  Quitter LScript")
        self.console.print(f"  [{self.theme.info}]help[/]        Afficher cette aide")
        self.console.print(f"  [{self.theme.info}]clear, cls[/]  Effacer l'écran")
        self.console.print(f"  [{self.theme.info}]cd <path>[/]   Changer de répertoire")
        self.console.print()
        self.console.print("[bold]Comment ça marche:[/bold]")
        self.console.print("  Tapez n'importe quelle commande shell.")
        self.console.print("  Si elle échoue, LScript explique l'erreur.")
        self.console.print()
        self.console.print(f"[dim]{rule_count} règles d'erreurs chargées[/dim]")
        self.console.print()
