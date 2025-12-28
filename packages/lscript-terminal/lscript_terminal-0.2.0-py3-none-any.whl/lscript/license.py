"""
Système de gestion de licence LScript.
"""
import os
from pathlib import Path

def get_license_path() -> Path:
    """Retourne le chemin du fichier de licence."""
    return Path.home() / ".lscript-license"

def has_valid_license() -> bool:
    """
    Vérifie si une licence valide est présente.
    Pour l'instant, vérifie juste l'existence du fichier.
    """
    license_path = get_license_path()
    if not license_path.exists():
        # Vérifie aussi variable d'env pour CI/Dev
        return os.environ.get("LSCRIPT_LICENSE") == "true"
        
    try:
        content = license_path.read_text().strip()
        return len(content) > 0
    except Exception:
        return False

def activate_license(key: str) -> bool:
    """Active une licence (mock)."""
    try:
        get_license_path().write_text(key)
        return True
    except Exception:
        return False
