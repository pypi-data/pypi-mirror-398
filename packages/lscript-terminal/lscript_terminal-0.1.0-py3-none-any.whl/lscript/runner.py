"""
Exécuteur de commandes shell.

Exécute les commandes via subprocess et capture
stdout, stderr et le code de retour.
"""

import subprocess
from dataclasses import dataclass


@dataclass
class CommandResult:
    """
    Résultat d'une exécution de commande.
    
    Attributes:
        command: La commande exécutée
        stdout: Sortie standard
        stderr: Sortie d'erreur
        return_code: Code de retour (0 = succès)
    """
    command: str
    stdout: str
    stderr: str
    return_code: int
    
    @property
    def success(self) -> bool:
        """Retourne True si la commande a réussi."""
        return self.return_code == 0


def run_command(command: str, timeout: int = 30) -> CommandResult:
    """
    Exécute une commande shell et capture le résultat.
    
    Args:
        command: La commande à exécuter
        timeout: Timeout en secondes
        
    Returns:
        CommandResult avec stdout, stderr et return_code
    """
    if not command or not command.strip():
        return CommandResult(
            command=command,
            stdout="",
            stderr="",
            return_code=0,
        )
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        
        return CommandResult(
            command=command,
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.returncode,
        )
        
    except subprocess.TimeoutExpired:
        return CommandResult(
            command=command,
            stdout="",
            stderr=f"Commande interrompue après {timeout} secondes",
            return_code=124,
        )
    except Exception as e:
        return CommandResult(
            command=command,
            stdout="",
            stderr=str(e),
            return_code=1,
        )
