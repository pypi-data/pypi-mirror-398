"""
Thèmes visuels pour LScript.

Ce module définit les thèmes de couleurs et styles
pour l'interface Rich.

Thèmes disponibles:
- DEFAULT_THEME: sobre et pédagogique (gratuit)
- DARK_THEME: mode sombre (premium)
- LIGHT_THEME: mode clair (premium)
- HACKER_THEME: style terminal vert (premium)
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    """
    Thème de couleurs pour l'interface LScript.
    
    Les couleurs utilisent la syntaxe Rich:
    - Noms: "red", "green", "cyan", etc.
    - Styles: "bold red", "dim white", etc.
    - Hex: "#ff5555"
    """
    name: str
    display_name: str
    description: str
    premium: bool = False
    
    # Couleurs principales
    error: str = "red"
    success: str = "green"
    info: str = "cyan"
    warning: str = "yellow"
    muted: str = "dim white"
    
    # Styles
    title: str = "bold"
    code: str = "bold white on grey23"
    prompt_ok: str = "bold green"
    prompt_error: str = "bold red"
    
    # Bordures des panels
    border_error: str = "red"
    border_info: str = "cyan"
    border_success: str = "green"


# =============================================================================
# THÈMES GRATUITS
# =============================================================================

DEFAULT_THEME = Theme(
    name="default",
    display_name="Défaut",
    description="Thème sobre et pédagogique, idéal pour les débutants",
    premium=False,
    # Palette One Dark inspirée
    error="#e06c75",        # Rouge doux
    success="#98c379",      # Vert doux
    info="#61afef",         # Bleu clair
    warning="#e5c07b",      # Jaune doux
    muted="dim",
    title="bold",
    code="bold",
    prompt_ok="bold #98c379",
    prompt_error="bold #e06c75",
    border_error="#e06c75",
    border_info="#61afef",
    border_success="#98c379",
)


# =============================================================================
# THÈMES PREMIUM
# =============================================================================

DARK_THEME = Theme(
    name="dark",
    display_name="Sombre",
    description="Mode sombre avec des couleurs vives",
    premium=True,
    error="#ff6b6b",
    success="#69db7c",
    info="#74c0fc",
    warning="#ffd43b",
    muted="dim white",
    title="bold",
    code="bold white on grey15",
    prompt_ok="bold #69db7c",
    prompt_error="bold #ff6b6b",
    border_error="#ff6b6b",
    border_info="#74c0fc",
    border_success="#69db7c",
)

LIGHT_THEME = Theme(
    name="light",
    display_name="Clair",
    description="Mode clair pour les écrans lumineux",
    premium=True,
    error="#c92a2a",
    success="#2f9e44",
    info="#1971c2",
    warning="#e67700",
    muted="dim black",
    title="bold",
    code="bold black on grey85",
    prompt_ok="bold #2f9e44",
    prompt_error="bold #c92a2a",
    border_error="#c92a2a",
    border_info="#1971c2",
    border_success="#2f9e44",
)

HACKER_THEME = Theme(
    name="hacker",
    display_name="Hacker",
    description="Style terminal vert classique",
    premium=True,
    error="#ff0000",
    success="#00ff00",
    info="#00ff00",
    warning="#ffff00",
    muted="dim green",
    title="bold green",
    code="bold green on black",
    prompt_ok="bold #00ff00",
    prompt_error="bold #ff0000",
    border_error="#ff0000",
    border_info="#00ff00",
    border_success="#00ff00",
)

DRACULA_THEME = Theme(
    name="dracula",
    display_name="Dracula",
    description="Thème populaire Dracula",
    premium=True,
    error="#ff5555",
    success="#50fa7b",
    info="#8be9fd",
    warning="#f1fa8c",
    muted="#6272a4",
    title="bold",
    code="bold #f8f8f2 on #282a36",
    prompt_ok="bold #50fa7b",
    prompt_error="bold #ff5555",
    border_error="#ff5555",
    border_info="#8be9fd",
    border_success="#50fa7b",
)


# =============================================================================
# REGISTRE DES THÈMES
# =============================================================================

THEMES: Dict[str, Theme] = {
    "default": DEFAULT_THEME,
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
    "hacker": HACKER_THEME,
    "dracula": DRACULA_THEME,
}


def get_theme(name: str) -> Theme:
    """
    Récupère un thème par son nom.
    
    Args:
        name: Nom du thème
        
    Returns:
        Le thème demandé, ou DEFAULT_THEME si non trouvé
    """
    return THEMES.get(name, DEFAULT_THEME)


def list_themes(include_premium: bool = True) -> list:
    """
    Liste tous les thèmes disponibles.
    
    Args:
        include_premium: Inclure les thèmes premium
        
    Returns:
        Liste des thèmes
    """
    if include_premium:
        return list(THEMES.values())
    return [t for t in THEMES.values() if not t.premium]
