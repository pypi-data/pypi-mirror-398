"""
Classes de base pour le système d'explication d'erreurs.

Ce module définit l'interface abstraite que les règles
doivent implémenter.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Explanation:
    """
    Explication d'une erreur.
    
    Attributes:
        title: Titre court de l'erreur
        message: Explication détaillée en langage simple
        suggestion: Action corrective concrète
    """
    title: str
    message: str
    suggestion: str


class ErrorRule(ABC):
    """
    Classe abstraite pour une règle d'explication d'erreur.
    
    Chaque règle sait:
    - Détecter si elle s'applique à une erreur (match)
    - Fournir une explication humaine (explain)
    """
    
    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Identifiant unique de la règle."""
        pass
    
    @abstractmethod
    def match(self, stderr: str, return_code: int) -> bool:
        """
        Teste si cette règle s'applique à l'erreur.
        
        Args:
            stderr: La sortie d'erreur de la commande
            return_code: Le code de retour
            
        Returns:
            True si cette règle peut expliquer l'erreur
        """
        pass
    
    @abstractmethod
    def explain(self, stderr: str, command: str) -> Explanation:
        """
        Génère une explication pour l'erreur.
        
        Args:
            stderr: La sortie d'erreur
            command: La commande qui a échoué
            
        Returns:
            Explanation avec titre, message et suggestion
        """
        pass
