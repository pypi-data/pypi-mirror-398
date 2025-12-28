"""
Module UI pour LScript.

Ce module fournit une couche de présentation
utilisant Rich pour un affichage moderne et lisible.

La logique métier (rules, runner) reste intacte.
"""

from lscript.ui.formatter import ErrorFormatter
from lscript.ui.theme import Theme, DEFAULT_THEME

__all__ = ["ErrorFormatter", "Theme", "DEFAULT_THEME"]
